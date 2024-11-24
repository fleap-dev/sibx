pub use compile_commands::CompileCommands;
pub use usage_storage::UsageStorage;

pub type Interval = rust_lapper::Interval<u32, String>;
pub type IntervalTree = rust_lapper::Lapper<u32, String>;

use std::ffi::OsStr;
use std::path::{Path, PathBuf};

mod compile_commands;
mod info;
mod usage_storage;

use info::Info;

const INFO_EXTENSION: &str = "o-info";

fn list_info_files(dir: &Path) -> Vec<PathBuf> {
    let ext = Some(OsStr::new(INFO_EXTENSION));

    let a = walkdir::WalkDir::new(dir)
        .into_iter()
        .filter_map(|dir_entry| {
            dir_entry
                .map(|e| {
                    if !e.file_type().is_dir() && e.path().extension() == ext {
                        Some(e.into_path())
                    } else {
                        None
                    }
                })
                .transpose()
        })
        .collect::<Result<Vec<_>, _>>();

    let a = a.unwrap();

    #[cfg(debug_assertions)]
    if a.is_empty() {
        log::warn!("No {INFO_EXTENSION} files found!");
    }

    a
}
