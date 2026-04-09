use rayon::prelude::*;
use pyo3::prelude::*;
use rand::seq::SliceRandom;
use std::collections::{HashMap, HashSet};

fn search(args: &Vec<String>, attacks: &HashMap<String, Vec<String>>, assignments: HashMap<String, Option<bool>>, new_assignment: Option<(&String, bool)>) -> Option<HashMap<String, Option<bool>>>    {
    let mut assignments = assignments.clone();
    if let Some((var, value)) = new_assignment {
        assignments = branch_and_propagate(attacks, assignments, (var.to_string(), value));
    }
    // pick random variable and assign a value
    let unassigned: Vec<&String> = assignments.iter()
                                .filter(|(_, val)| val.is_none())
                                .map(|(key, _)| key)
                                .collect();
    if unassigned.is_empty() {
        // all variables are assigned, check if the assignment is a stable extension
        // check if everthing else is attacked by some argument in the stable extension
        for arg in args {
            if assignments.get(arg) == Some(&Some(false)) {
                // if arg is not in the extension, check if it is attacked by some argument in the extension
                let attackers: Vec<&String> = attacks.iter()
                                                .filter(|(_, targets)| targets.contains(&arg))
                                                .map(|(attacker, _)| attacker)
                                                .collect();
                let attacked = attackers.iter().any(|a| assignments.get(a.as_str()) == Some(&Some(true)));
                if !attacked { return None; }
            }
        }
        // if we reach here, we found a stable extension
        return Some(assignments); // return the stable extension
    }
    // TODO: implement a better heuristic for variable selection
    let selected_var: String = (*unassigned.choose(&mut rand::thread_rng())?).clone();
    drop(unassigned);
    let branching_assignments = vec![
        (selected_var.clone(), true),
        (selected_var.clone(), false)
    ];

    return branching_assignments.par_iter().map(|(var, value)| {
        search(args, attacks, assignments.clone(), Some((var, *value)))
    }).find_any(|res| res.is_some()).flatten();
}

fn branch_and_propagate(attacks: &HashMap<String, Vec<String>>, mut assignments: HashMap<String, Option<bool>>, new_assignment: (String, bool)) -> HashMap<String, Option<bool>> {
    let (selected_var, selected_value) = new_assignment;
    // propagate implications of the assignment
    assignments.iter_mut().for_each(|(key, value)| {
        if *key == selected_var {
            *value = Some(selected_value);
        }
    });

    if selected_value {
        for (arg, targets) in attacks {
            if *arg == selected_var {
                for target in targets {
                    // selected_var is true, so everything it attacks must be false
                    assignments.iter_mut().for_each(|(name, value)| {
                        if name == target {
                            *value = Some(false);
                        }
                    });
                }
            } else if targets.contains(&selected_var) {
                // selected_var is true, so anything attacking it must be false (conflict-free)
                assignments.iter_mut().for_each(|(key, value)| {
                    if *key == *arg {
                        *value = Some(false);
                    }
                });
            }
        }
    }
    return assignments;
}

#[pyfunction]
fn compute_stable_extension(args: Vec<String>, attacks: HashMap<String, Vec<String>>) -> PyResult<HashSet<String>> {
    let mut temp_assignments = HashMap::new();
    for arg in &args {
        temp_assignments.insert(arg.clone(), None);
    }
    let assignments = search(&args, &attacks, temp_assignments, None);
    let mut stable_extension = HashSet::new();
    if let Some(assignments) = assignments {
        for (key, value) in assignments {
            if value == Some(true) {
                stable_extension.insert(key.clone());
            }
        }
    }
    Ok(stable_extension)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn make_assignments(args: &[&str]) -> HashMap<String, Option<bool>> {
        args.iter().map(|a| (a.to_string(), None)).collect()
    }

    fn make_attacks(pairs: &[(&str, &str)]) -> HashMap<String, Vec<String>> {
        let mut map: HashMap<String, Vec<String>> = HashMap::new();
        for (attacker, target) in pairs {
            map.entry(attacker.to_string()).or_default().push(target.to_string());
        }
        map
    }

    fn in_extension(result: &Option<HashMap<String, Option<bool>>>, name: &str) -> bool {
        result.as_ref().unwrap().get(name) == Some(&Some(true))
    }

    // No arguments, no attacks → empty set is the unique stable extension
    #[test]
    fn empty_framework() {
        let result = search(&vec![], &HashMap::new(), make_assignments(&[]), None);
        assert!(result.is_some());
        assert!(result.unwrap().is_empty());
    }

    // Single argument with no attacks → {a} is the unique stable extension
    #[test]
    fn single_unattacked_arg() {
        let args = vec!["a".to_string()];
        let result = search(&args, &HashMap::new(), make_assignments(&["a"]), None);
        assert!(result.is_some());
    }

    // Mutual attack a↔b → exactly one of {a} or {b} is returned
    #[test]
    fn mutual_attack() {
        let args = vec!["a".to_string(), "b".to_string()];
        let attacks = make_attacks(&[("a", "b"), ("b", "a")]);
        let result = search(&args, &attacks, make_assignments(&["a", "b"]), None);
        assert!(result.is_some());
        let ext = result.unwrap();
        let a_in = ext.iter().any(|(k, v)| k == "a" && *v == Some(true));
        let b_in = ext.iter().any(|(k, v)| k == "b" && *v == Some(true));
        assert!(a_in ^ b_in, "exactly one of a or b should be in the extension");
    }

    // Chain a→b→c → unique stable extension is {a, c}
    #[test]
    fn chain() {
        let args = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        let attacks = make_attacks(&[("a", "b"), ("b", "c")]);
        let result = search(&args, &attacks, make_assignments(&["a", "b", "c"]), None);
        assert!(in_extension(&result, "a"));
        assert!(!in_extension(&result, "b"));
        assert!(in_extension(&result, "c"));
    }

    // 4-cycle a→b→c→d→a → two stable extensions {a,c} or {b,d}
    #[test]
    fn four_cycle() {
        let args = vec!["a".to_string(), "b".to_string(), "c".to_string(), "d".to_string()];
        let attacks = make_attacks(&[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]);
        let result = search(&args, &attacks, make_assignments(&["a", "b", "c", "d"]), None);
        assert!(result.is_some());
        let ext = result.unwrap();
        let a = ext.get("a") == Some(&Some(true));
        let b = ext.get("b") == Some(&Some(true));
        let c = ext.get("c") == Some(&Some(true));
        let d = ext.get("d") == Some(&Some(true));
        assert!((a && c && !b && !d) || (b && d && !a && !c), "expected {{a,c}} or {{b,d}}");
    }

    // Self-attacking argument → no stable extension exists
    #[test]
    fn self_attack() {
        let args = vec!["a".to_string()];
        let attacks = make_attacks(&[("a", "a")]);
        let result = search(&args, &attacks, make_assignments(&["a"]), None);
        assert!(result.is_none());
    }
}
