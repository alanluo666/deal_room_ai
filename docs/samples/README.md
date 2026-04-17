# Demo sample documents

Synthetic documents used by `DEMO.md` to exercise Deal Room AI
end-to-end. **All content is fictional.** Company names (including
"Acme Corp", "AcmeClose", "BlueHarbor Industrials", and "Lexton
Accounting Group"), financial figures, litigation details, and
operational facts are invented for demonstration purposes only. Do not
rely on any of these files for real-world analysis.

Files

- `acme_q1_brief.txt` — plain-text internal diligence brief.
- `acme_risk_factors.docx` — Word document listing fictional risk
  factors.
- `acme_prospectus.pdf` — single-page PDF summarizing a fictional
  offering.

To regenerate (for example after editing the content in `_generate.py`):

```bash
python docs/samples/_generate.py
```

The generator uses only dependencies already listed in
`requirements.txt` (`python-docx`; the PDF is built by hand to avoid
adding `reportlab`).
