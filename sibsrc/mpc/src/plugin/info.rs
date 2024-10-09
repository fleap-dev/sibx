use std::path::PathBuf;

use serde::Deserialize;

use crate::interval::Interval;

#[derive(Debug, Deserialize)]
pub struct Info {
    pub tu: PathBuf,
    pub args: String,
    pub files: Vec<File>,
}

#[derive(Debug, Deserialize)]
pub struct File {
    pub lines: u32,
    pub path: PathBuf,

    pub skips: Vec<Interval>,
}
