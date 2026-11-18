#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:globals.glsl>
#include <minecraft:light.glsl>
#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <minecraft:sample_lightmap.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;
layout(location = 3) in ivec2 UV1;
layout(location = 4) in ivec2 UV2;
#ifdef GLINT_SPECIAL
layout(location = 5) in vec2 UV3;
#endif
layout(location = 6) in vec3 Normal;

#ifndef OIT_ALPHA_ONLY
uniform sampler2D Sampler1;
uniform sampler2D Sampler2;

layout(location = 0) out float sphericalVertexDistance;
layout(location = 1) out float cylindricalVertexDistance;
#endif
layout(location = 2) out vec4 vertexColor;
#ifndef OIT_ALPHA_ONLY
layout(location = 3) out vec4 lightMapColor;
layout(location = 4) out vec4 overlayColor;
#endif

layout(location = 5) out vec2 texCoord0;
#ifdef GLINT
layout(location = 6) out vec2 texCoordGlint;
#endif

// ---------------------------------------------------------------------------
// tc-create kinetic parts.
//
// A rotating part of a Create block is an item display whose model tints
// every face with custom model data color 0. The plot packs the part's spin
// into that color (tc/render.tc, kineticTint), and this shader turns the
// part here, so the plot never animates spinning parts itself:
//
//   bits 23..18  000001 (marker: red channel 4..7)
//   bits 17..16  rotation axis: 0 x, 1 y, 2 z (3: not rotated)
//   bit  15      large cogwheel (half-tooth base offset, 11.25 degrees)
//   bits 14..13  pivot block mod 4 on the first axis across the rotation axis
//   bits 12..11  pivot block mod 4 on the second axis across it
//   bits 10..0   speed in half RPM, two's complement (-512 .. 511.5 RPM)
//
// The pivot is the center of the part's block. Across the axis, its block
// coordinate is the one nearest to the vertex that has the given value mod 4
// (every part reaches less than 2 blocks from its pivot). Along the axis the
// pivot does not matter.
//
// The angle is Create's own (KineticBlockEntityRenderer.getAngleForBe):
// render ticks * RPM * 0.3 degrees, plus 22.5 degrees when the two block
// coordinates across the axis add up to an even number, else 11.25 for a
// large cogwheel and 0 for anything else. It turns right-handed about the
// positive axis. So meshing cogwheels line up the way they do in Create.
// ---------------------------------------------------------------------------

const int KINETIC_MARKER = 1;

void kinetic_turn(inout vec3 pos, inout vec3 nrm, inout vec4 col) {
    ivec3 c8 = ivec3(round(col.rgb * 255.0));
    int code = (c8.r << 16) | (c8.g << 8) | c8.b;
    if ((code >> 18) != KINETIC_MARKER || col.a < 0.99) {
        return;
    }
    col = vec4(1.0);
    int axis = (code >> 16) & 3;
    if (axis == 3) {
        return;
    }
    int large = (code >> 15) & 1;
    int pa = (code >> 13) & 3;
    int pb = (code >> 11) & 3;
    int sp = code & 2047;
    if (sp >= 1024) {
        sp -= 2048;
    }
    float rpm = float(sp) * 0.5;

    int ia = axis == 0 ? 1 : 0;
    int ib = axis == 2 ? 1 : 2;

    // this vertex relative to the camera's block
    vec3 rel = pos - CameraOffset;
    int ba = CameraBlockPos[ia];
    int bb = CameraBlockPos[ib];
    int ma = (pa - ba) & 3;
    int mb = (pb - bb) & 3;
    float na = round((rel[ia] - 0.5 - float(ma)) / 4.0);
    float nb = round((rel[ib] - 0.5 - float(mb)) / 4.0);
    int blockA = ba + ma + 4 * int(na);
    int blockB = bb + mb + 4 * int(nb);
    float ca = float(ma) + 4.0 * na + 0.5;
    float cb = float(mb) + 4.0 * nb + 0.5;

    float deg = ((blockA + blockB) & 1) == 0 ? 22.5 : (large == 1 ? 11.25 : 0.0);
    float ticks = GameTime * 24000.0;
    deg += mod(ticks * rpm * 0.3, 360.0);
    float ang = radians(deg);
    float c = cos(ang);
    // turning about +y is (z, x) in right-handed order, the others (a, b)
    float s = axis == 1 ? -sin(ang) : sin(ang);

    float a = rel[ia] - ca;
    float b = rel[ib] - cb;
    pos[ia] += (a * c - b * s) - a;
    pos[ib] += (a * s + b * c) - b;

    float n0 = nrm[ia];
    float n1 = nrm[ib];
    nrm[ia] = n0 * c - n1 * s;
    nrm[ib] = n0 * s + n1 * c;
}

void main() {
    vec3 pos = Position;
    vec3 nrm = Normal;
    vec4 col = Color;
    kinetic_turn(pos, nrm, col);

    gl_Position = ProjMat * ModelViewMat * vec4(pos, 1.0);

    #ifndef OIT_ALPHA_ONLY
    sphericalVertexDistance = fog_spherical_distance(pos);
    cylindricalVertexDistance = fog_cylindrical_distance(pos);
    #endif
    vertexColor = minecraft_mix_light(Light0_Direction, Light1_Direction, nrm, col);
    #ifndef OIT_ALPHA_ONLY
    lightMapColor = sample_lightmap(Sampler2, UV2);
    overlayColor = texelFetch(Sampler1, UV1, 0);
    #endif

    texCoord0 = UV0;
    #ifdef GLINT
    #ifdef GLINT_SPECIAL
    texCoordGlint = (TextureMat * vec4(UV3, 0.0, 1.0)).xy;
    #else
    texCoordGlint = (TextureMat * vec4(UV0, 0.0, 1.0)).xy;
    #endif
    #endif
}
