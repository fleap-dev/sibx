use crate::plugin::Interval;

#[derive(Debug)]
pub struct Hunk {
    pub old_lines: Interval,
}

impl From<git2::DiffHunk<'_>> for Hunk {
    fn from(diff_hunk: git2::DiffHunk) -> Self {
        let old_begin = diff_hunk.old_start();

        // If a change consists just of added lines, `diff_hunk.old_lines()` is 0.
        // However, since we are using [start,end) intervals, for a hunk to be changed, end must be greater (not equal!) than begin.
        let old_end = old_begin + std::cmp::max(diff_hunk.old_lines(), 1);
        debug_assert!(old_begin < old_end);

        Self {
            old_lines: Interval {
                start: old_begin,
                stop: old_end, // +1 not necessary, hunks are also [a, b)
                val: String::new(),
            },
        }
    }
}

use core::fmt;

impl fmt::Display for Hunk {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}:{}]", self.old_lines.start, self.old_lines.stop)
    }
}
