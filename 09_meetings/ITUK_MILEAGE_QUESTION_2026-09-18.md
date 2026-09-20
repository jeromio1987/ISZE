# ITUK — average annual mileage of the N-series fleet

**Draft for Jerome. Not sent.** This is copy-paste only — Jerome sends from Outlook.

---

## Why the question is being asked

The PRISM parts-capture model applies **50,000 km/year** to the UK truck parc. Measured against real
odometer readings in the CV warranty claims, the UK N-series figures are **16,688 km/yr across all
classes** and **35,478 km/yr for N75 alone** — a third to two-thirds of the assumption.

On the current mileage base the model multiplies expected service demand by roughly **1.4× on N75**
and **3.0× on N35** above what the odometers show. If the 50,000 is right, UK capture has been
*overstated* and nothing needs to change in the market conversation. If the odometers are right, UK
capture is *understated* and the UK service opportunity is larger than we present.

**The warranty file cannot settle it, and it is the wrong instrument to try.** It only contains
vehicles that made a warranty claim, and only over a 28-month window. It is the best measurement we
have, but it is not a fleet survey.

What Duncan already gave us and what is still missing:

| Item | Status |
|---|---|
| VIN list (29,935 VINs, model label + registration date) | **Have it** — 23 Jul 2026 |
| Odometer / km reading of any kind | **Not in the file** — no mileage column exists |
| Annual distance per vehicle or per model | **Missing** — this question |

So the only thing needed is one number per model family, from ITUK's own records.

---

## Draft mail

**Subject:** N-series average annual mileage — UK parc

```
Hello Duncan,

One number would close a question we cannot settle from our side.

Our parts model applies 50,000 km a year to the UK N-series parc. When we measure real odometer
readings in the warranty claims, the UK figures come out at about 16,700 km a year across all
classes, and 35,500 km for N75 on its own. That is a third to two-thirds of the assumption, and it
is the difference between UK service demand being larger or smaller than we currently show.

Your VIN file has no mileage column, so I cannot get this from the data you sent.

Could you give me the average annual mileage of the N-series parc, and if you have it, split by
N35 and N75? Even a rough figure from your service records or from the dealer network would be
better than the assumption we are using now.

Many thanks and kind regards,

Jérôme Van der Pluym
Assistant Manager // Pricing analyst
Sales – Vehicle Parts | Isuzu Motors Europe NV
+32 475 851 089
jerome.van.der.pluym@isuzu-e.com
Bist 12, 2630 Aartselaar, Belgium
```

---

## Notes before sending

- **To:** Duncan Young, Parts Director, Isuzu Truck UK. **Do not send** — Jerome sends.
- Do not attach the warranty extract. It carries claim-level detail that should not leave the
  workspace; the question stands on its own.
- If Duncan answers with a single blended number, ask for the N35/N75 split only if it matters for
  the decision — otherwise take the blended figure and record it as market-stated.
- The same question was put to **UTI (Israel)**, whose 50,000 km/yr the odometers **confirmed**
  (51,680 measured). The point of the mail is that we asked both markets the same way, and one
  answered differently from the other.

Source of the measured figures: `01_data\90_INBOX\_cv_warranty_mileage_validation.md` (Method C,
odometer at claim ÷ years since retail) and the independent 2–3 year odometer check in
`01_data\90_INBOX\_ld_weight_class_and_wallet_correction_20260918.md` §3.
