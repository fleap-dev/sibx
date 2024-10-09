use serde::Deserialize;
use serde::Serialize;

#[derive(Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub struct Interval {
    pub begin: u32,
    pub end: u32,
}

impl Interval {
    pub fn new(begin: u32, end: u32) -> Self {
        debug_assert!(begin <= end, "{begin} > {end}");
        Self { begin, end }
    }

    /// inverts *sorted* intervals
    pub fn invert(intervals: &[Interval], end: u32) -> Vec<Interval> {
        Self::debug_assert_sorted(intervals);

        let mut inverted = Vec::with_capacity(intervals.len() + 1);
        let mut last = 1;
        for inter in intervals {
            if inter.begin > 1 && inter.begin > last {
                inverted.push(Interval::new(last, inter.begin - 1));
            }

            last = inter.end + 1;

            if inter.end == end {
                break;
            }
        }
        if last <= end {
            inverted.push(Interval::new(last, end));
        }

        debug_assert_eq!(
            inverted.capacity(),
            intervals.len() + 1,
            "Wrong capacity expectations"
        );
        inverted
    }

    fn debug_assert_sorted<A>(intervals: &[A])
    where
        A: AsRef<Interval> + std::fmt::Debug,
    {
        if cfg!(debug_assertions) {
            let mut iter = intervals.iter().peekable();
            while let Some(interval) = iter.next() {
                if let Some(next_interval) = iter.peek() {
                    debug_assert!(interval.as_ref().begin <= next_interval.as_ref().begin);
                }
            }
        }
    }
}

use core::convert;
impl convert::AsRef<Interval> for Interval {
    fn as_ref(&self) -> &Interval {
        self
    }
}

use core::fmt;
impl fmt::Display for Interval {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{},{}]", self.begin, self.end)
    }
}
impl fmt::Debug for Interval {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{self}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_invert_1() {
        let intervals = vec![
            Interval::new(1, 3),
            Interval::new(5, 6),
            Interval::new(9, 10),
        ];
        assert_eq!(
            Interval::invert(&intervals, 10),
            vec![Interval::new(4, 4), Interval::new(7, 8)]
        );
    }

    #[test]
    fn test_invert_2() {
        let intervals = vec![Interval::new(2, 3)];
        assert_eq!(
            Interval::invert(&intervals, 4),
            vec![Interval::new(1, 1), Interval::new(4, 4)]
        );
    }

    #[test]
    fn test_invert_3() {
        let intervals = vec![Interval::new(2, 3), Interval::new(3, 4)];
        assert_eq!(Interval::invert(&intervals, 4), vec![Interval::new(1, 1)]);
    }

    #[test]
    #[should_panic]
    fn test_invert_unsorted() {
        let intervals = vec![Interval::new(4, 5), Interval::new(2, 3)];

        Interval::invert(&intervals, 4);
    }
}
