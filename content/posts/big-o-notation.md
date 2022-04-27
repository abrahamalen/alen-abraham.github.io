---
title: "Big O notation explained: DSA-01"
date: 2022-03-14T12:56:25+05:30
weight: 160
draft: false
summary: "A brief explanation on Big O notation in Data Structures and Algorithms with examples."
#tags: ["dsa"]
categories: ["dsa","tutorial"]
aliases: [/dsa]
featuredImage: "/images/big-o-notation/cover-image.png"  
cover:
  image: "/images/big-o-notation/cover-image.png"
  alt: "Photo of big O notation"
 # caption: "Photo by [Canva Studio](https://www.pexels.com/@canvastudio) from [Pexels](https://www.pexels.com/photo/photo-of-man-using-laptop-3194523/)"
  relative: false
---  

## What is Big O notation?  

**Big O notation** is used to measure how the running time or space requirements for our program grows as input grows.

- Measuring running time growth is time complexity. (In this post we focus on time complexity)
- Measuring space growth is space complexity.  

## Rules to determine time complexity

1. Keep fastest growing term.
2. Drop constants.  

Big O refers to very large value of 'n' (n = size) where time, **t = an^2 + bn + c**.  
For example, if we have a function like,
> t = 5n^2 + 3n + 20  

When value of 'n' is very large, bn+c becomes irrelevant.   
ie; an^2 is very larger than bn+c.  
For example; if n = 1000 then,  
t = 5 * 1000^2 + 3*1000+20 = 5000000 + 3020; where 3020, a small value becomes irrelevant.  

## Different time complexities  
Here we discuss about a few of them.

#### 1. O(n)  
> def foo(arr): size(arr) -> 100 -> 0.22ms  
> def foo(arr): size(arr) -> 1000 -> 2.30ms  

Here time increases as array size increases; time proportional to size(arr).  
n = size(arr), b= constant  
t = a*n + b  
1. Keep fastest growing term => t = a * n (b is constant)  
2. Drop constants => t = n ( a is constant)  
Therefore; **t = O(n)**  

*Example program for t = O(n): To get square numbers*
```
def get_squared_numbers(numbers):
    squared_numbers = []
    for n in numbers:
        square_numbers.append(n * n)
    return squared_numbers

numbers = [2, 5, 8, 9]
get_squared_numbers(numbers)
// returns [4, 25, 64, 81]
```

#### 2. O(1)  
> def foo(arr): size(arr) -> 100 -> 0.22ms  
> def foo(arr): size(arr) -> 1000 -> 0.23ms    

time, t = a * n + b -> t = a * n ( b constant) -> t = n (dropping constants(a))  
n = 1 => t = 1  
Therefore, **t = O(1)**  

*Example program for t = O(1)*  
```
def find_first_pe(prices, eps, index):
    pe = prices[index]/eps[index]
    return pe
```
#### 3. O(n^2)  
*Example Program for O(n^2): To find duplicates from the list*
```
numbers = [3, 6, 2, 4, 3, 6, 8, 9]

for i in range(len(numbers)):
    for j in range(i + 1, len(numbers)):
        if numbers[i] == numbers[j]:
            print(numbers[i] + " is a duplicate.")
            break
```

## A table of common Big - O functions.  

 | Big O       | Name        |  
 | :---------- | :---------- |  
 | 1           | Constant    |  
 | log(n)      | Logarithmic |  
 | n           | Linear      |  
 | nlog(n)     | Log linear  |  
 | n^2         | Quadratic   |  
 | n^3         | Cubic       |  
 | 2^n         | Exponential |

For more reference go through these -   
- [Big-O Notation Explained](https://stackoverflow.com/questions/487258/what-is-a-plain-english-explanation-of-big-o-notation/487278#487278)  
- [Big-O Examples Explained](https://stackoverflow.com/questions/2307283/what-does-olog-n-mean-exactly)

Thank you for the read.  
Repost on [Hashnode](https://alenabraham.hashnode.dev/big-o-notation-explained-dsa-01) & [Dev](https://dev.to/alenabraham/big-o-notation-explained-dsa-01-4oag) 

