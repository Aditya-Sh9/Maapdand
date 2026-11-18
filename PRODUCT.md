# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: Legal Metrology enforcement officials (inspectors) who screen many packaged products and need to focus on the ones likely to be non-compliant. The problem statement (SIH26034, Ministry of Consumer Affairs, Food & Public Distribution) frames the product around "enforcement officials" and "inspections".
Secondary: manufacturers, packers, importers and online sellers who want to self-check a label before printing or listing.

## Product Purpose
Checks packaged-product labels against the Legal Metrology (Packaged Commodities) Rules, 2011. Gives a Pass / Fail / Cannot determine verdict for each rule, with the evidence marked on the label image. Success means an inspector can tell which declarations are missing or wrong, and why, within a minute of photographing a pack.

## Positioning
A screening aid, not a legal determination. Final authority stays with the inspector. Every verdict is tied to a verified clause of the Rules and to the exact spot on the image where the evidence was found. "Cannot determine" is reported openly and never hidden behind a false pass.

## Operating Context
Inspectors are in the field or at a desk with a phone or laptop, photographing packs (several images per product). Labels mix English and Hindi. Lighting is uneven and images may be glared or blurred. A human reviews and corrects the extracted fields before the final verdict.

## Capabilities and Constraints
- Pipeline: upload images or paste text, then OCR (Tesseract, English + Hindi), field extraction, human review, rule checks, and a report (PDF planned).
- 12 rules (R01–R10, M01–M02). M01/M02 (font height, principal display panel) currently return Cannot determine.
- The interface is English only. Label content may be Devanagari.
- Built with Django templates + vanilla JS, with no build step. The demo must work offline (self-hosted assets).
- In the problem statement but out of v1: dashboards, scan history, role-based access, editable export formats.

## Brand Commitments
Name: Maapdand (मापदंड, "standard / yardstick"). Wording is calm, plain and official. Never imply legal certainty.

## Evidence on Hand
Gazette PDFs and a rule-to-clause mapping in docs/reference/. No accuracy figures, testimonials or user counts exist yet; none may be invented.

## Product Principles
1. Never fake a pass: three-state verdicts, with a bias toward flagging.
2. Show the evidence next to every claim.
3. A human confirms what the machine read.
4. Explainable end to end: every verdict traces to a clause.

## Accessibility & Inclusion
WCAG AA basics: contrast, keyboard use, visible focus, labels, reduced motion, verdicts never shown by colour alone. Devanagari must render correctly.
