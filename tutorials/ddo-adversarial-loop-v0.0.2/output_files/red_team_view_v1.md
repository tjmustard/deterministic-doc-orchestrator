# Red Team Report v1

**Persona:** scientific_reviewer  
**Document:** output/copolyester-optimization.md  
**Timestamp:** 2026-06-29T20:10:00Z  
**Total Findings:** 5

---

## Critical (2)

### F-001 `[decision_recorded, applied]`

**Category:** Overreaching Conclusions  
**Location:** 6. Conclusion

**Description:** The report recommends PX-104 as the optimal candidate, but recomputing the paper's own objective function Z = 0.3*S + 0.4*Y - 0.1*T - 0.2*E on the Phase II data ranks PX-104 third (45.96), behind PX-103 (51.12) and PX-105 (46.44). The stated conclusion is not supported by the stated methodology.

**Suggestion:** Tabulate the computed Z for all candidates and recommend the true maximum, or correct the objective function/weights so the model actually selects PX-104, and state which.

### F-002 `[decision_recorded]`

**Category:** Methodological Vagueness  
**Location:** 3. Methodology

**Description:** The toxicity term -w_t*T_i is sign-inverted relative to the stated goal of minimizing toxicity. LD50 is inversely related to toxicity (a higher LD50 is safer), so subtracting it penalizes safer candidates and effectively maximizes toxicity.

**Suggestion:** Replace LD50 with a monotonic toxicity index, or add (rather than subtract) a transformed safety term, and re-derive Z.

## Major (2)

### F-003 `[decision_recorded]`

**Category:** Statistical Ambiguity  
**Location:** 3. Methodology

**Description:** The methodology claims 'normalized weights', but the variables are never normalized before the weighted sum. Raw solubility (12-88 mg/L) dwarfs ecology impact (1.8-4.2 kg CO2/kg), so the composite is dominated by magnitude, not by the intended weighting.

**Suggestion:** Apply min-max or z-score normalization to each metric before weighting, and report the normalized values.

### F-004 `[decision_recorded, applied]`

**Category:** Unsupported Assertions  
**Location:** 4. Discussion

**Description:** The claim that gas chromatography indicates unreacted monomer residues in PX-103 cites no entry in the evidence_bank; the supporting GC dataset is not referenced.

**Suggestion:** Add the GC-MS residual-monomer dataset to the evidence_bank and reference it from the discussion.

## Minor (1)

### F-005 `[decision_recorded]`

**Category:** Missing Limitations  
**Location:** 5. Conclusion

**Description:** No limitations are acknowledged: replicate counts, sample sizes, and confidence intervals for the murine LD50 assays are absent, so the reproducibility and statistical strength of the toxicity figures cannot be assessed.

**Suggestion:** Add a limitations subsection stating n, replicate counts, and CIs for the LD50 measurements.
