use std::path::{Path, PathBuf};

use rayon::prelude::*;
use serde::Deserialize;
use serde::Serialize;

use crate::helper::*;
use crate::CheckpointArgs;

#[derive(Debug, Deserialize, Serialize)]
pub struct Checkpoint {
    file_hashes: Vec<(PathBuf, Digest)>,
}

impl Checkpoint {
    pub fn create(args: &CheckpointArgs) -> Result<(), std::io::Error> {
        // map files to (path, hash)
        let file_hashes = args
            .file
            .iter()
            .map(|file| {
                let file = if file.is_relative() {
                    args.dir.join(file)
                } else {
                    file.to_path_buf()
                };

                let content = std::fs::read(&file)?;
                let hash = hash_fn(&content);

                Ok((file, hash))
            })
            .collect::<Result<Vec<_>, std::io::Error>>()?;

        let checkpoint = Checkpoint { file_hashes };

        Self::dump(&checkpoint, args)
    }

    fn dump(data: &Checkpoint, args: &CheckpointArgs) -> Result<(), std::io::Error> {
        let serialized = if cfg!(debug_assertions) {
            serde_json::to_string_pretty(data)?
        } else {
            serde_json::to_string(data)?
        };

        let version = args.commit.as_ref().unwrap();
        let filename = if let Some(variant) = &args.variant {
            format!("extra-{version}-{variant}.json")
        } else {
            format!("extra-{version}.json")
        };
        let path = args.storage.join(filename);
        std::fs::write(path, serialized)
    }

    fn list_dir<P: AsRef<Path>>(dir: P) -> Result<Vec<PathBuf>, std::io::Error> {
        let res = walkdir::WalkDir::new(dir)
            .into_iter()
            .filter_map(|dir_entry| {
                dir_entry
                    .map(|e| {
                        if !e.file_type().is_dir() {
                            Some(e.into_path())
                        } else {
                            None
                        }
                    })
                    .transpose()
            })
            .collect::<Result<Vec<_>, _>>()?;

        Ok(res)
    }

    fn find_variants_for_commit(dir: &Path, commit: &str) -> Option<(String, String, Checkpoint)> {
        let (version, variant) = dir
            .file_stem()
            .unwrap()
            .to_str()
            .unwrap()
            .split_once('-')
            .unwrap();

        if version.starts_with(&("extra-".to_owned() + commit)) {
            let content = std::fs::read_to_string(dir).unwrap();
            let compact: Checkpoint = serde_json::from_str(&content).unwrap();
            Some((version.to_owned(), variant.to_owned(), compact))
        } else {
            None
        }
    }

    fn is_affected(checkpoint: &Checkpoint) -> bool {
        checkpoint.file_hashes.iter().any(|(file, hash)| {
            let new_content = std::fs::read(file).unwrap();
            let new_hash = hash_fn(&new_content);

            *hash != new_hash
        })
    }

    pub fn find_affected_variants<P: AsRef<Path>>(
        dir: P,
        commit: &str,
    ) -> Result<Vec<String>, std::io::Error> {
        let _res = Self::list_dir(&dir)?
            .into_par_iter()
            .filter_map(|path| Self::find_variants_for_commit(&path, commit))
            .filter(|(_, _, checkpoint)| Self::is_affected(checkpoint))
            .map(|(_, variant, _)| variant)
            .collect/*::<Result<_, _>>*/();

        panic!("checkpointing using the new format not supported yet");

        Ok(_res)
    }
}
