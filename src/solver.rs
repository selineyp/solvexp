use pyo3::prelude::*;
use rand::seq::SliceRandom;
use std::collections::{HashMap, HashSet};

fn search(args: &Vec<String>, attacks: &HashMap<String, Vec<String>>, assignments: HashMap<String, Option<bool>>, newAssignment: Option<(&String, bool)>) -> Option<HashMap<String, Option<bool>>>    {
    let mut assignments = assignments.clone();
    if let Some((var, value)) = newAssignment {
        assignments = branchAndPropagate(attacks, assignments, (var.to_string(), value));
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
    let selectedVar: String = (*unassigned.choose(&mut rand::thread_rng())?).clone();
    drop(unassigned);
    let lhsRes: Option<HashMap<String, Option<bool>>> = search(&args, &attacks, assignments.clone(), Some((&selectedVar, true)));
    let rhsRes: Option<HashMap<String, Option<bool>>> = search(&args, &attacks, assignments.clone(), Some((&selectedVar, false)));

    // TODO: implement logic to combine results from both branches
    if let Some(res) = lhsRes {
        return Some(res);
    }
    if let Some(res) = rhsRes {
        return Some(res);
    }
    return None;
}

fn branchAndPropagate(attacks: &HashMap<String, Vec<String>>, mut assignments: HashMap<String, Option<bool>>, newAssignment: (String, bool)) -> HashMap<String, Option<bool>> {
    let (selectedVar, selectedValue) = newAssignment;
    // propagate implications of the assignment
    assignments.iter_mut().for_each(|(key, value)| {
        if *key == selectedVar {
            *value = Some(selectedValue);
        }
    });

    if selectedValue {
        for (arg, targets) in attacks {
            if *arg == selectedVar {
                for target in targets {
                    // selectedVar is true, so everything it attacks must be false
                    assignments.iter_mut().for_each(|(name, value)| {
                        if name == target {
                            *value = Some(false);
                        }
                    });
                }
            } else if targets.contains(&selectedVar) {
                // selectedVar is true, so anything attacking it must be false (conflict-free)
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
fn computeStableExtension(args: Vec<String>, attacks: HashMap<String, Vec<String>>) -> PyResult<HashSet<String>> {
    // Implement a simple DPLL algorithm with propagation
    // This is a placeholder for the actual implementation
    let mut tempAssignments = HashMap::new();
    // initialize tempAssignments with the variables from the problem
    for arg in &args {
        tempAssignments.insert(arg.clone(), None);
    }
    let assignments = search(&args, &attacks, tempAssignments, None);
    let mut stableExtension = HashSet::new();
    if let Some(assignments) = assignments {
        for (key, value) in assignments {
            if value == Some(true) {
                stableExtension.insert(key.clone());
            }
        }
    }
    Ok(stableExtension)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn makeAssignments(args: &[&str]) -> HashMap<String, Option<bool>> {
        args.iter().map(|a| (a.to_string(), None)).collect()
    }

    fn makeAttacks(pairs: &[(&str, &str)]) -> HashMap<String, Vec<String>> {
        let mut map: HashMap<String, Vec<String>> = HashMap::new();
        for (attacker, target) in pairs {
            map.entry(attacker.to_string()).or_default().push(target.to_string());
        }
        map
    }

    fn inExtension(result: &Option<HashMap<String, Option<bool>>>, name: &str) -> bool {
        result.as_ref().unwrap().get(name) == Some(&Some(true))
    }

    // No arguments, no attacks → empty set is the unique stable extension
    #[test]
    fn emptyFramework() {
        let result = search(&vec![], &HashMap::new(), makeAssignments(&[]), None);
        assert!(result.is_some());
        assert!(result.unwrap().is_empty());
    }

    // Single argument with no attacks → {a} is the unique stable extension
    #[test]
    fn singleUnattackedArg() {
        let args = vec!["a".to_string()];
        let result = search(&args, &HashMap::new(), makeAssignments(&["a"]), None);
        assert!(result.is_some());
    }

    // Mutual attack a↔b → exactly one of {a} or {b} is returned
    #[test]
    fn mutualAttack() {
        let args = vec!["a".to_string(), "b".to_string()];
        let attacks = makeAttacks(&[("a", "b"), ("b", "a")]);
        let result = search(&args, &attacks, makeAssignments(&["a", "b"]), None);
        assert!(result.is_some());
        let ext = result.unwrap();
        let aIn = ext.iter().any(|(k, v)| k == "a" && *v == Some(true));
        let bIn = ext.iter().any(|(k, v)| k == "b" && *v == Some(true));
        assert!(aIn ^ bIn, "exactly one of a or b should be in the extension");
    }

    // Chain a→b→c → unique stable extension is {a, c}
    #[test]
    fn chain() {
        let args = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        let attacks = makeAttacks(&[("a", "b"), ("b", "c")]);
        let result = search(&args, &attacks, makeAssignments(&["a", "b", "c"]), None);
        assert!(inExtension(&result, "a"));
        assert!(!inExtension(&result, "b"));
        assert!(inExtension(&result, "c"));
    }

    // 4-cycle a→b→c→d→a → two stable extensions {a,c} or {b,d}
    #[test]
    fn fourCycle() {
        let args = vec!["a".to_string(), "b".to_string(), "c".to_string(), "d".to_string()];
        let attacks = makeAttacks(&[("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")]);
        let result = search(&args, &attacks, makeAssignments(&["a", "b", "c", "d"]), None);
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
    fn selfAttack() {
        let args = vec!["a".to_string()];
        let attacks = makeAttacks(&[("a", "a")]);
        let result = search(&args, &attacks, makeAssignments(&["a"]), None);
        assert!(result.is_none());
    }
}
