// Copyright (c) Facebook, Inc. and its affiliates. (http://www.facebook.com)
#ifndef __JIT_HIR_ALIAS_CLASS_H__
#define __JIT_HIR_ALIAS_CLASS_H__

#include "Jit/hir/type.h"

#include <cstdint>
#include <iosfwd>

namespace jit {
namespace hir {

// AliasClass is a lattice of memory locations describing where instructions
// can read from or write to. It is similar to hir::Type, but much simpler.
//
// The implementation exposes its internal bitvector as a uint64_t, for
// consumers that want to combine it with other bits in a larger bitvector.

// Disjoint locations that each get one bit in the bitvector.
#define HIR_BASIC_ACLS(X) \
  X(ArrayItem)            \
  X(CellItem)             \
  X(FuncArgs)             \
  X(FuncAttr)             \
  X(Global)               \
  X(InObjectAttr)         \
  X(ListItem)             \
  X(Other)                \
  X(TupleItem)            \
  X(TypeAttrCache)

// Predefined unions.
#define HIR_UNION_ACLS(X)                           \
  /* Bottom union */                                \
  X(Empty, 0)                                       \
  /* Top union */                                   \
  X(Any, 0 HIR_BASIC_ACLS(HIR_OR_BITS))             \
  /* Memory locations accessible by managed code */ \
  X(ManagedHeapAny, kAny & ~kFuncArgs)

#define HIR_ACLS(X) HIR_BASIC_ACLS(X) HIR_UNION_ACLS(X)

class AliasClass {
  enum BitIndexes {
#define ACLS(name) k##name##Bit,
    HIR_BASIC_ACLS(ACLS)
#undef ACLS
  };

 public:
#define ACLS(name) +1
  static constexpr size_t kNumBits = HIR_BASIC_ACLS(ACLS);
#undef ACLS
  static constexpr size_t kBitsMask = (1ull << kNumBits) - 1;

  using bits_t = uint64_t;

#define ACLS(name) static constexpr bits_t k##name = 1ULL << k##name##Bit;
  HIR_BASIC_ACLS(ACLS)
#undef ACLS
#define ACLS(name, bits) static constexpr bits_t k##name = (bits);
  HIR_UNION_ACLS(ACLS)
#undef ACLS

  explicit constexpr AliasClass(bits_t bits) : bits_{bits} {}

  bool operator==(AliasClass other) const {
    return bits_ == other.bits_;
  }
  bool operator!=(AliasClass other) const {
    return !operator==(other);
  }

  bool operator<=(AliasClass other) const {
    return (bits_ & other.bits_) == bits_;
  }
  bool operator<(AliasClass other) const {
    return *this <= other && *this != other;
  }

  AliasClass operator&(AliasClass other) const {
    return AliasClass{bits_ & other.bits_};
  }
  AliasClass operator|(AliasClass other) const {
    return AliasClass{bits_ | other.bits_};
  }

  std::string toString() const;

  bits_t bits() const {
    return bits_;
  }

 private:
  static_assert(kNumBits <= sizeof(bits_t) * CHAR_BIT, "Too many bits");
  bits_t bits_;
};

// Similar to Type, create a constant prefixed with A for all predefined
// AliasClasses.
#define ACLS(name, ...) constexpr AliasClass A##name{AliasClass::k##name};
HIR_ACLS(ACLS)
#undef ACLS

std::ostream& operator<<(std::ostream& os, const AliasClass& acls);

} // namespace hir
} // namespace jit

template <>
struct std::hash<jit::hir::AliasClass> {
  size_t operator()(const jit::hir::AliasClass& acls) const {
    return acls.bits();
  }
};

#endif
