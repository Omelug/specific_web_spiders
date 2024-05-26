while read -r word; do
  echo -n "${word}"
  echo ">[^>]*${word}[^<]*<"
  cat * | grep -r -i -Po ">[^>]*${word}[^<]*<"
done < words.txt