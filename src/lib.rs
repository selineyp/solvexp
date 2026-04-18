use pyo3::prelude::*;

mod solver;

/// Rust-side solver module, exposed to Python as `solvexp._solver`.
/// Extension computation algorithms will live here.
#[pymodule]
fn _solver(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(solver::compute_stable_extension, m)?)?;
    Ok(())
}
