# IR_HW2

## 功能說明
### 1. Search : 
* #### 可搜尋一篇文章中的關鍵字 及 搜尋在資料庫中所有文章中和關鍵字相同或類似的字。
* #### 實現partial match 以及 Porter's algorithm 和 MED。
* #### 實現利用index進行搜尋。
### 2. Statistic : 
#### 分兩部分統計:
* #### 其一為分析所有文章中的word，計算其frequency (zipf) : 利用直方圖視覺化。
* #### 另一為個別分析每一文章中的word，判斷哪一個word的tf-idf較高，並為之排序 : 利用折線圖視覺化。

## 功能意義說明:
### 1. Search:
* #### 想在search上，能做出和google初步相同的東西，也就是可以搜尋資料並在資料庫當中尋找，並為每一個字設定index，以利後續highlight的動作
### 2. Statistic : 
* #### 在zipf中，可以得到每一個字出現的頻率，也就代表他在這些資料當中的重要程度比較大，前提是去除stopwords的狀況。
* #### 而tf-idf則可以表達在每一篇文章中，各個字所能代表這篇文章的重要性有少，當然現在有很多人認為tf-idf不是一個很好的衡量工具，但在初學階段是一個可以用來簡單分析的方法。
