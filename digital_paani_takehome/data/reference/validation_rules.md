# Design data validation rules

*Notes from the water & wastewater domain team, for DP-DE-TH-01. Written as prose on
purpose — turning this into something a program can execute is part of the task.*

---

## How we think about these

Two different things get called "validation" around here and it's worth keeping them
apart. The first is a plausibility band on a single reported number: inlet COD of
14,000 mg/L in a residential building means somebody wrote the wrong thing down, and we
don't need any other data point to know that. The second is a design-adequacy check,
where we take two or three reported numbers and ask whether they can all be true at
once — a tank whose stated volume doesn't match its stated dimensions, for instance.
The second kind is the more useful of the two and also the more annoying, because a
failing check tells you something is wrong without telling you which of the numbers is
the wrong one.

One important convention: for the design-adequacy checks we allow a **10% margin on
each side of the stated band** before we call something a problem. Surveyors are
pacing out tanks with their feet, and we would rather not flag a tank that is 3%
short. The plausibility bands on individual numbers are applied as stated, without
the extra margin.

Nothing here should ever cause a record to be thrown away silently. A number we can't
justify is still a number somebody walked around a plant to collect.

---

## Plausibility bands on individual values

A handful of quantities simply cannot be negative, and a zero or negative value means
a transcription problem rather than a real measurement. That applies to both flow
figures, the freshwater cost, every one of the consumption and reuse volumes, the tank
count, all four tank dimensions, and the cable run distance to the panel.

For the wastewater quality figures we have bands from years of looking at Indian STPs
and ETPs. On the **inlet** side, COD should land between 300 and 1,000 mg/L (400–600
is the usual range for a non-industrial plant), BOD between 100 and 600 mg/L (150–450
typical), total nitrogen between 10 and 100 mg/L (20–85 typical), and TSS between 100
and 500 mg/L. Inlet pH we only bound at 1 to 14, because industrial inlets genuinely
do go to both extremes — though anything outside 6.5–8.5 at a domestic sewage plant is
worth a second look even if it doesn't trip the rule.

On the **outlet** side the bands are tighter because the plant is supposed to be
hitting a discharge norm: COD 22.5–82.5 mg/L (we design for 25–75), BOD 4.5–22 mg/L
(5–20 typical), total nitrogen 0.9–11 mg/L (1–10 typical), and TSS 9–33 mg/L (10–30
typical).

The **freshwater** figures have their own bands. TDS should be 45–275 mg/L for a
municipal or surface source; note that borewell water in much of India runs well
above this and can reach 1,000 mg/L, so a high TDS on a borewell site is usually a
real reading rather than an error — the rule will still fire, and that is fine, it is
telling you to go and check. pH is bounded 0–14 and in practice should be 6.5–8.5.
Hardness should be 9–198 mg/L as CaCO₃ (10–180 is the usual spread, occasionally to
300). Fluoride should be 0.009–0.33 mg/L, again with the caveat that groundwater in
parts of Rajasthan and Gujarat will exceed 10 mg/L.

Two more. The fraction of treated water reused on site is a fraction, so it lives
between 0 and 1 — if somebody has written a percentage in that column you have a
problem to solve before the rule can even be applied. And TDS measured at the reuse
points should be 450–1,100 mg/L for treated non-industrial wastewater.

---

## Design adequacy checks

### Peaking factor

Divide the observed peak inlet flow by the average treatment volume. The result should
be between **2.0 and 4.5**. Below 2 usually means somebody has reported the same
number twice, or reported an average where a peak was asked for. Above 4.5 nearly
always means a unit error or a decimal in the wrong place — a genuine peaking factor
above 5 would imply a plant that is idle most of the day and then takes a slug of flow
it was never designed for, which does happen at, say, a stadium, but not at the sites
we work on. With the 10% margin the effective band is 1.8 to 4.95.

### Collection tank sizing

The collection tank is the buffer between whatever arrives at the plant and the first
treatment step, so it needs to hold enough to ride out a short interruption. Our
sizing convention is that the tank should hold at least **10 minutes of flow at the
plant's design capacity**, where design capacity is spread over an assumed **20 hours
of daily operation** rather than 24 — plants here do not run round the clock.

So: take the design flow in kL/d, divide by 20 to get the hourly rate, then divide by
6 to get 10 minutes' worth. The total collection tank volume (per-tank volume
multiplied by the number of tanks) must be at least that figure. A plant treating
1,200 kL/d needs 1,200 ÷ 20 ÷ 6 = 10 m³ of collection tank; if the survey reports 1.8
m³ then either the tank is genuinely undersized, which is a finding the retrofit team
needs, or the surveyor measured the wrong tank.

### Tank count versus arrangement

Surveyors record how many tanks of a type there are, and separately record the
physical arrangement as rows × columns. Multiply the rows by the columns and it should
equal the count. When it doesn't, one of the two was recorded for a different tank, or
a tank was added later and only one field got updated.

### Reported volume versus reported dimensions

For a **rectangular** tank, length × width × height should reproduce the reported
volume. For a **cylindrical** tank, π ÷ 4 × diameter² × height should reproduce it.
Both within the 10% margin — the dimensions are paced or tape-measured and the volume
is often read off a drawing, so exact agreement is not expected. A large disagreement
usually means the volume came from a design document describing a tank that was never
built as drawn, which is exactly the kind of thing we want to know before we quote a
retrofit.

Note that the shape field decides which of the two checks applies, and that a tank
with a zero or missing dimension can't be checked at all — the check should be skipped
in that case, not failed.

---

## Things that are not rules, but you should still surface them

Values that repeat across two sheets and disagree. Client names that don't match
between sheets. Anything numeric that arrived as text. Blank cells in a field the
survey app marks as required. None of these have a benchmark attached; they are still
data quality problems and the onboarding team would rather hear about them from you
than from a customer.
