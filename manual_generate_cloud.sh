# loop through the subdirectories 
for filename in sentences/**/*.csv; do
  $filename%.* (removes file path)
  wordcloud_cli --text $filename --imagefile word_clouds/${filename##*/}.png 
done

# loop through csv files in the current directory
for filename in sentences/*.csv; do
  $filename%.* (removes file path)
  wordcloud_cli --text $filename --imagefile word_clouds/${filename##*/}.png 
done
