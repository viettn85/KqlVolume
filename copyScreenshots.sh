#!/bin/bash

image_location="/Users/viet_tran/Google Drive/Working/Trading/Stock/Screenshots/"
stock_location="/Users/viet_tran/Workplace/kql/KqlVolume/stocks/"
custom_stock_location="stocks/"

stockLists=("vn30"  "consider"  "ducky"  "following"  "portfolio"  "down"  "top" "bottom" "bank" "bds" "stock")
 
# Print array values in  lines
echo "Print every element in new line"
for stockList in ${stockLists[*]}; do
      echo ${stockList}
      rm -f "${image_location}${stockList}/*.png"
      input="${stock_location}${stockList}.csv"
      while IFS= read -r line
      do
        echo "$line"
        cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
      done < "$input"
done
