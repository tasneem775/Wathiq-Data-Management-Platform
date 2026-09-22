from pathlib import Path

p = Path(r".\wathiq_portfolio_package\04_Platform_Mockups\meyar_platform_mockups.html")

text = p.read_text(encoding="utf-8")

backup = p.with_name("meyar_platform_mockups_before_dcm4_remove.html")
backup.write_text(text, encoding="utf-8")

# remove CSS
start = text.find("<!-- Added block — DC.M.4 Review Report")
end = text.find("</style>", start)

if start != -1 and end != -1:
    text = text[:start] + text[end+8:]

# remove view
start = text.find("<!-- ============ VIEW 6 (added)")
end = text.find("</section>", start)

if start != -1 and end != -1:
    text = text[:start] + text[end+10:]

# remove JS
start = text.find("<!-- Added block — wiring for the new DC.M.4")
end = text.find("</script>", start)

if start != -1 and end != -1:
    text = text[:start] + text[end+9:]

p.write_text(text, encoding="utf-8")

print("DONE")
print(backup)