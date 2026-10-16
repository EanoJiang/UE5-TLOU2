// Rewrite this pipeline's static, identity-transform Blender OCurves archive
// into the UE Groom schema without modifying its raw centimeter coordinates.
// Usage: groom_abc_attributes.exe input.abc output.abc
// Refuses animation, nonidentity transforms, unsupported curves and overwrites.
#include <Alembic/AbcGeom/All.h>
#include <Alembic/AbcCoreOgawa/All.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace A = Alembic::Abc;
namespace G = Alembic::AbcGeom;
namespace O = Alembic::AbcCoreOgawa;

struct Shape {
    int group = -1;
    std::string name, source_path;
    std::vector<Imath::V3f> positions;
    std::vector<int32_t> counts;
    std::vector<float> widths;
    G::GeometryScope width_scope = G::kUnknownScope;
    Imath::Box3d bounds;
};

struct Duplicate { int group; std::string kept, removed; size_t curves, points; };
std::vector<Duplicate> duplicates;
size_t raw_curve_count = 0, raw_point_count = 0;

void require(bool ok, const std::string& message) {
    if (!ok) throw std::runtime_error(message);
}

int group_from_name(const std::string& path) {
    const std::vector<std::string> names{"thick", "thin", "flyaway", "wet"};
    for (size_t i = 0; i < names.size(); ++i)
        if (path.find(names[i]) != std::string::npos ||
            path.find("group_" + std::to_string(i)) != std::string::npos) return int(i);
    throw std::runtime_error("Unknown Groom group in " + path);
}

void read_shapes(A::IObject object, std::vector<Shape>& shapes, bool standard) {
    if (G::IXform::matches(object.getHeader())) {
        G::IXform xform(object, A::kWrapExisting);
        require(xform.getSchema().getNumSamples() == 1,
                "Only static transforms supported: " + object.getFullName());
        auto matrix = xform.getSchema().getValue().getMatrix();
        for (int row = 0; row < 4; ++row) for (int col = 0; col < 4; ++col)
            require(std::abs(matrix[row][col] - double(row == col)) < 1e-10,
                    "Nonidentity transform would change geometry: " + object.getFullName());
    } else if (G::ICurves::matches(object.getHeader())) {
        G::ICurves curves(object, A::kWrapExisting);
        auto& schema = curves.getSchema();
        require(schema.getNumSamples() == 1, "Only one static geometry sample supported");
        auto sample = schema.getValue();
        require(sample.getType() == G::kLinear && sample.getWrap() == G::kNonPeriodic &&
                sample.getBasis() == G::kNoBasis, "Expected linear nonperiodic POLY curves");
        Shape shape;
        shape.group = group_from_name(object.getFullName());
        shape.name = std::vector<std::string>{"thick", "thin", "flyaway", "wet"}[shape.group];
        shape.source_path = object.getFullName();
        auto positions = sample.getPositions();
        auto counts = sample.getCurvesNumVertices();
        shape.positions.assign(positions->get(), positions->get() + positions->size());
        shape.counts.assign(counts->get(), counts->get() + counts->size());
        size_t total = 0;
        for (auto count : shape.counts) {
            require(count == 24, "Expected exactly 24 points per reconstructed strand");
            total += size_t(count);
        }
        require(total == shape.positions.size(), "Curve vertex counts do not sum to positions");
        shape.bounds.makeEmpty();
        for (const auto& p : shape.positions) {
            require(std::isfinite(p.x) && std::isfinite(p.y) && std::isfinite(p.z), "Nonfinite position");
            shape.bounds.extendBy(Imath::V3d(p));
        }
        auto widths = schema.getWidthsParam();
        require(widths.valid(), "Source curve widths missing");
        auto values = widths.getExpandedValue().getVals();
        shape.widths.assign(values->get(), values->get() + values->size());
        shape.width_scope = widths.getScope();
        require(shape.widths.size() == shape.positions.size(), "Expected one width per point");
        for (float width : shape.widths)
            require(std::isfinite(width) && width > 0, "Invalid source width");
        if (standard) {
            auto params = schema.getArbGeomParams();
            G::IInt32GeomParam group(params, "groom_group_id");
            require(group.valid() && group.getScope() == G::kConstantScope,
                    "Missing constant .arbGeomParams groom_group_id");
            auto groups = group.getExpandedValue().getVals();
            require(groups->size() == 1 && (*groups)[0] == shape.group, "Group ID value mismatch");
            G::IFloatGeomParam groom_width(params, "groom_width");
            require(groom_width.valid() && groom_width.getScope() == G::kVertexScope,
                    "Missing vertex-scope groom_width");
            auto groom_widths = groom_width.getExpandedValue().getVals();
            require(groom_widths->size() == shape.widths.size() &&
                    std::memcmp(groom_widths->get(), shape.widths.data(), shape.widths.size() * sizeof(float)) == 0,
                    "Explicit groom_width differs from standard curve width");
        }
        shapes.push_back(std::move(shape));
    } else {
        require(object.getFullName() == "/", "Unexpected noncurve object: " + object.getFullName());
    }
    for (size_t child = 0; child < object.getNumChildren(); ++child)
        read_shapes(object.getChild(child), shapes, standard);
}

std::vector<Shape> read_archive(const std::string& path, bool standard = false) {
    A::IArchive archive(O::ReadArchive(), path);
    std::vector<Shape> shapes;
    read_shapes(archive.getTop(), shapes, standard);
    std::sort(shapes.begin(), shapes.end(), [](const Shape& a, const Shape& b) { return a.group < b.group; });
    if (!standard) {
        std::vector<Shape> unique;
        for (auto& shape : shapes) {
            raw_curve_count += shape.counts.size();
            raw_point_count += shape.positions.size();
            if (!unique.empty() && unique.back().group == shape.group) {
                const auto& kept = unique.back();
                require(shape.counts.size() == kept.counts.size() &&
                        shape.positions.size() == kept.positions.size() &&
                        shape.widths.size() == kept.widths.size(), "Same-group shapes have different counts");
                require(std::memcmp(shape.counts.data(), kept.counts.data(), shape.counts.size() * sizeof(int32_t)) == 0 &&
                        std::memcmp(shape.widths.data(), kept.widths.data(), shape.widths.size() * sizeof(float)) == 0,
                        "Same-group shapes have different topology or widths; cannot deduplicate");
                for (size_t p = 0; p < shape.positions.size(); ++p) {
                    const auto& a = shape.positions[p]; const auto& b = kept.positions[p];
                    require(std::memcmp(&a.x, &b.x, sizeof(float)) == 0 &&
                            std::memcmp(&a.y, &b.y, sizeof(float)) == 0 &&
                            std::memcmp(&a.z, &b.z, sizeof(float)) == 0,
                            "Same-group shapes have different point bits; cannot deduplicate");
                }
                duplicates.push_back({shape.group, kept.source_path, shape.source_path,
                                      shape.counts.size(), shape.positions.size()});
            } else unique.push_back(std::move(shape));
        }
        shapes = std::move(unique);
    }
    require(shapes.size() == 4, "Expected exactly four source OCurves groups");
    for (int i = 0; i < 4; ++i) require(shapes[i].group == i, "Expected one shape per group 0..3");
    return shapes;
}

void write_archive(const std::string& path, const std::vector<Shape>& shapes) {
    A::OArchive archive(O::WriteArchive(), path);
    G::OXform root(archive.getTop(), "groom");
    root.getSchema().set(G::XformSample());
    auto user = root.getSchema().getUserProperties();
    A::OInt16Property(user, "groom_version_major").set(1);
    A::OInt16Property(user, "groom_version_minor").set(5);
    A::OStringProperty(user, "groom_tool").set("Capture card reconstruction; native Alembic 1.8.9 schema adapter");
    A::OStringProperty(user, "groom_properties").set("Static actor-local UE centimeters; reconstructed fibers; no binding or simulation");
    for (const auto& shape : shapes) {
        G::OCurves curves(root, "group_" + std::to_string(shape.group));
        auto& schema = curves.getSchema();
        // Blender 4.5's exporter can leave the width scope unspecified. The
        // length proves per-point storage; normalize metadata to vertex scope.
        G::OFloatGeomParam::Sample widths(A::FloatArraySample(shape.widths), G::kVertexScope);
        G::OCurvesSchema::Sample sample(A::P3fArraySample(shape.positions), A::Int32ArraySample(shape.counts),
            G::kLinear, G::kNonPeriodic, widths, G::OV2fGeomParam::Sample(),
            G::ON3fGeomParam::Sample(), G::kNoBasis);
        sample.setSelfBounds(shape.bounds);
        schema.set(sample);
        auto params = schema.getArbGeomParams();
        const int32_t id = shape.group, guide = 0;
        G::OInt32GeomParam group(params, "groom_group_id", false, G::kConstantScope, 1);
        group.set(G::OInt32GeomParam::Sample(A::Int32ArraySample(&id, 1), G::kConstantScope));
        G::OStringGeomParam name(params, "groom_group_name", false, G::kConstantScope, 1);
        name.set(G::OStringGeomParam::Sample(A::StringArraySample(&shape.name, 1), G::kConstantScope));
        G::OInt32GeomParam guides(params, "groom_guide", false, G::kConstantScope, 1);
        guides.set(G::OInt32GeomParam::Sample(A::Int32ArraySample(&guide, 1), G::kConstantScope));
        G::OFloatGeomParam groom_width(params, "groom_width", false, G::kVertexScope, 1);
        groom_width.set(widths);
    }
}

uint64_t hash_bytes(uint64_t hash, const void* memory, size_t bytes) {
    const auto* ptr = static_cast<const unsigned char*>(memory);
    for (size_t i = 0; i < bytes; ++i) { hash ^= ptr[i]; hash *= 1099511628211ull; }
    return hash;
}

std::string geometry_hash(const Shape& shape) {
    uint64_t hash = 14695981039346656037ull;
    for (const auto& position : shape.positions) {
        hash = hash_bytes(hash, &position.x, sizeof(float));
        hash = hash_bytes(hash, &position.y, sizeof(float));
        hash = hash_bytes(hash, &position.z, sizeof(float));
    }
    hash = hash_bytes(hash, shape.counts.data(), shape.counts.size() * sizeof(int32_t));
    hash = hash_bytes(hash, shape.widths.data(), shape.widths.size() * sizeof(float));
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << hash;
    return out.str();
}

void emit_report(const std::vector<Shape>& before, const std::vector<Shape>& after) {
    size_t curves = 0, points = 0;
    std::cout << std::setprecision(10) << "{\"pass\":true,\"unique_geometry_bitwise_unchanged\":true,\"input_raw_curve_count\":"
              << raw_curve_count << ",\"input_raw_point_count\":" << raw_point_count
              << ",\"duplicate_source_shapes_removed\":[";
    for (size_t i = 0; i < duplicates.size(); ++i) {
        const auto& duplicate = duplicates[i];
        if (i) std::cout << ',';
        std::cout << "{\"group_id\":" << duplicate.group << ",\"kept_path\":\"" << duplicate.kept
                  << "\",\"removed_path\":\"" << duplicate.removed << "\",\"curve_count\":" << duplicate.curves
                  << ",\"point_count\":" << duplicate.points << ",\"all_array_bits_equal\":true}";
    }
    std::cout << "],\"groups\":[";
    for (size_t i = 0; i < before.size(); ++i) {
        const auto& a = before[i];
        const auto& b = after[i];
        require(geometry_hash(a) == geometry_hash(b), "Geometry/width hash mismatch after rewriting");
        require(a.counts == b.counts && a.positions.size() == b.positions.size() && a.widths == b.widths,
                "Array counts or values changed");
        for (size_t p = 0; p < a.positions.size(); ++p)
            require(a.positions[p] == b.positions[p], "Point value changed");
        if (i) std::cout << ',';
        std::cout << "{\"group_id\":" << a.group << ",\"name\":\"" << a.name
                  << "\",\"curve_count\":" << a.counts.size() << ",\"point_count\":" << a.positions.size()
                  << ",\"source_width_scope\":" << int(a.width_scope)
                  << ",\"output_width_scope\":" << int(b.width_scope)
                  << ",\"group_scope\":\"constant\",\"groom_width_scope\":\"vertex\",\"geometry_fnv1a64\":\""
                  << geometry_hash(a) << "\",\"width_cm_min_max\":[" << *std::min_element(a.widths.begin(), a.widths.end())
                  << ',' << *std::max_element(a.widths.begin(), a.widths.end()) << "],\"bounds_cm\":[["
                  << a.bounds.min.x << ',' << a.bounds.min.y << ',' << a.bounds.min.z << "],["
                  << a.bounds.max.x << ',' << a.bounds.max.y << ',' << a.bounds.max.z << "]]}";
        curves += a.counts.size(); points += a.positions.size();
    }
    std::cout << "],\"curve_count\":" << curves << ",\"point_count\":" << points << "}\n";
}

int main(int argc, char** argv) {
    try {
        require(argc == 3, "usage: groom_abc_attributes.exe input.abc output.abc");
        require(std::filesystem::exists(argv[1]), "Input archive missing");
        require(!std::filesystem::exists(argv[2]), "Output already exists; refusing overwrite");
        auto original = read_archive(argv[1]);
        write_archive(argv[2], original);
        auto rewritten = read_archive(argv[2], true);
        emit_report(original, rewritten);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "groom_abc_attributes: " << e.what() << '\n';
        return 1;
    }
}
