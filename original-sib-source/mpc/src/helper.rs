#[cfg(feature = "murmur3")]
use std::io::Cursor;

#[cfg(feature = "murmur3")]
pub type Digest = u128;

#[cfg(feature = "xxhash3")]
pub type Digest = u64;

#[cfg(all(feature = "murmur3", feature = "xxhash3"))]
compile_error!("feature \"murmur3\" and feature \"xxhash3\" cannot be enabled at the same time");

#[inline]
pub fn hash_fn(data: &[u8]) -> Digest {
    #[cfg(feature = "murmur3")]
    return murmur3::murmur3_x64_128(&mut Cursor::new(data), 0).unwrap();

    #[cfg(feature = "xxhash3")]
    return twox_hash::xxh3::hash64(data);
}
