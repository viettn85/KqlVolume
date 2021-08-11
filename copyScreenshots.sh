#!/bin/bash

image_location="/Users/viet_tran/Google Drive/Working/Trading/Stock/Screenshots/"
stock_location="/Users/viet_tran/Workplace/kql/data/stock/"
custom_stock_location="stocks/"

stockList="vn30"
echo stockList
rm -f "${image_location}${stockList}/*.png"
input="${stock_location}${stockList}.csv"
while IFS= read -r line
do
  echo "$line"
  cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
done < "$input"

stockList="ducky"
echo stockList
rm -f "${image_location}${stockList}/*.png"
input="${stock_location}${stockList}.csv"
while IFS= read -r line
do
  echo "$line"
  cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
done < "$input"

stockList="following"
echo stockList
rm -f "${image_location}${stockList}/*.png"
input="${custom_stock_location}${stockList}.csv"
while IFS= read -r line
do
  echo "$line"
  cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
done < "$input"

stockList="sideway"
echo stockList
rm -f "${image_location}${stockList}/*.png"
input="${stock_location}${stockList}.csv"
while IFS= read -r line
do
  echo "$line"
  cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
done < "$input"

stockList="potentials"
echo stockList
rm -f "${image_location}${stockList}/*.png"
input="${stock_location}${stockList}.csv"
while IFS= read -r line
do
  echo "$line"
  cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
done < "$input"

stockList="miss_entry"
echo stockList
rm -f "${image_location}${stockList}/*.png"
input="${stock_location}${stockList}.csv"
while IFS= read -r line
do
  echo "$line"
  cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
done < "$input"

stockList="portfolio"
echo stockList
rm -f "${image_location}${stockList}/*.png"
input="${custom_stock_location}${stockList}.csv"
while IFS= read -r line
do
  echo "$line"
  cp "${image_location}daily/${line}.png" "${image_location}${stockList}"
done < "$input"