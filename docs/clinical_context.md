# Clinical context (DRAFT: not yet reviewed or cited)

## Why length of stay matters
Hospital beds are a limited resource. When patients stay longer than clinically necessary, beds are
not available for the next patient, which contributes to delays in emergency departments and
elective surgery, and keeps patients exposed to hospital risks (such as infection, falls and
deconditioning) for longer. _[citations needed: ACSQHC / AIHW / Queensland Health sources, to be added and verified]_

## What is missing from a plain "average stay" number
An average length of stay (LOS) hides a lot. A cardiac ward with a long average stay may simply
be treating sicker patients. The useful question is: **is this stay longer than expected for
patients like this one?** This project answers that by comparing each stay with its peers
(same diagnosis category and age band) and summing the difference as **excess bed-days**.

## Where communication fits in
Delayed discharge often has a communication component (waiting on reviews, results, transport or
community supports being coordinated). The ieMR records an Estimated Date of Discharge (EDD) for
planning, but a displayed LOS does not show whether a stay is longer than expected for the
patient's condition. _(Based on the author's student-nurse experience of the ieMR; to be checked.)_

## What this dashboard is, and is not
- **Is:** a demonstration of a benchmarking method on synthetic data, with design choices
  explained (leave-one-out mean, O/E ratio, minimum peer-group size).
- **Is not:** a finding about real hospitals. Patients in this dataset were assigned to fictional
  hospitals at random, so differences between hospitals are noise by design.
- Cancer readmissions are retained but flagged as likely planned treatment cycles.

## Design principles
One screen, no tabs, few controls, colour reserved for what needs attention.
(Informed by the author's experience of dense clinical systems.)
