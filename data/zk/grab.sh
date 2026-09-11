for s in rikeisuugaku butsuri kagaku eigo; do
  curl -s --max-time 30 "https://www.zkai.co.jp/kyodai-exam/bunseki/$s/" -o "${s}-2026.html"
  for y in 2025 2024 2023 2022 2021 2020 2019 2018; do
    curl -s --max-time 30 "https://www.zkai.co.jp/kyodai-exam/bunseki/$s-$y/" -o "${s}-${y}.html"
  done
done
ls -la *.html | head -50
