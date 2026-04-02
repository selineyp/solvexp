use pyo3::prelude::*;

mod solver;

/// Rust-side solver module, exposed to Python as `solvexp._solver`.
/// Extension computation algorithms will live here.
#[pymodule]
fn _solver(_m: &Bound<'_, PyModule>) -> PyResult<()> {
    Ok(())
}
