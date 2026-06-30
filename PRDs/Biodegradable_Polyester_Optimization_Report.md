# **Multi-Parameter Optimization of Aliphatic-Aromatic Copolyesters for Sustainable Packaging**

## **1\. Abstract**

The transition to sustainable consumer packaged goods (CPG) requires polymers that balance mechanical durability with rapid environmental degradability. This report details the evaluation of five aliphatic-aromatic copolyester candidates (PX-101 through PX-105). Through multi-parameter optimization—balancing solubility, synthesizability, toxicity, and ecological impact—we identify a pre-optimized blend capable of commercial scaling while maintaining stringent environmental safety profiles.

## **2\. Introduction**

Current petrochemical-derived packaging materials exhibit exceptional barrier properties and high synthesis yields but persist in the environment for centuries. While biodegradable alternatives exist, they often suffer from low synthesizability (yield) or unacceptably high ecological footprints during manufacturing. This study evaluates five novel copolyester blends, aiming to maximize manufacturing yield and marine solubility while minimizing mammalian toxicity and carbon footprint.

## **3\. Methodology**

Candidate selection relies on a composite desirability function. We evaluate the candidates across four primary metrics. The objective function Z is calculated using normalized weights for each parameter:  
Z \= \\sum\_{i=1}^{n} \\left( w\_s S\_i \+ w\_y Y\_i \- w\_t T\_i \- w\_e E\_i \\right)  
Where:

* S\_i \= Water Solubility (mg/L), indicating degradation rate in marine environments.  
* Y\_i \= Synthesizability Yield (%), indicating manufacturing efficiency.  
* T\_i \= Toxicity LD50 (g/kg), measured via murine models.  
* E\_i \= Ecology Impact (kg \\text{CO}\_2/kg resin), tracking lifecycle emissions.

For this evaluation, we apply a commercially balanced weighting scheme: w\_s \= 0.3, w\_y \= 0.4, w\_t \= 0.1, and w\_e \= 0.2.

## **4\. Dataset**

The following table summarizes the raw empirical data collected during the Phase II trials.  
**Table 1: Candidate Polymer Evaluation Metrics**

| Polymer ID | Yield (%) Y | Solubility (mg/L) S | Toxicity LD50 (g/kg) T | Ecology Impact (kg \\text{CO}\_2/kg) E |
| :---- | :---- | :---- | :---- | :---- |
| PX-101 | 82.0 | 45.0 | 12.5 | 4.2 |
| PX-102 | 91.5 | 12.0 | 18.0 | 2.1 |
| PX-103 | 64.0 | 88.0 | 5.2 | 1.8 |
| PX-104 | 88.5 | 42.0 | 15.4 | 2.5 |
| PX-105 | 75.0 | 60.0 | 9.8 | 2.9 |

*(Note for Visualization: Generate a dual-axis bar chart comparing Yield and Toxicity, and a scatter plot mapping Solubility against Ecology Impact).*

## **5\. Example Findings and Discussion**

Based on the empirical data and the objective function Z, we observe several critical structure-property trade-offs:

1. **The Synthesizability vs. Degradability Trade-off:** There is a distinct inverse correlation between manufacturing yield and water solubility. Candidate **PX-102** achieved the highest yield (91.5\\%) but exhibited the lowest solubility (12.0 mg/L), suggesting highly crystalline domains that resist hydrolysis. Conversely, **PX-103** is highly amorphous and soluble (88.0 mg/L) but suffers from poor yield (64.0\\%) and higher toxicity.  
2. **Toxicity and Precursor Residue:** **PX-103** demonstrated the highest toxicity (lowest LD50 at 5.2 g/kg). Gas chromatography indicates this is likely due to unreacted monomer residues trapped within the amorphous polymer matrix, directly correlating with its low synthesizability yield.  
3. **Optimal Candidate Identification:** Applying the objective function Z, **PX-104** emerges as the optimal candidate. While it does not possess the absolute highest solubility or yield individually, it successfully bridges the performance gap. It achieves a commercially viable yield (88.5\\%) while maintaining adequate solubility (42.0 mg/L) and a low carbon footprint (2.5 kg \\text{CO}\_2/kg).

## **6\. Conclusion**

Candidate **PX-104** represents the most balanced copolyester for CPG applications. We recommend advancing PX-104 to Phase III pilot plant scaling. Future work will focus on optimizing the catalyst to push the solubility boundary of PX-104 closer to 50.0 mg/L without sacrificing yield.