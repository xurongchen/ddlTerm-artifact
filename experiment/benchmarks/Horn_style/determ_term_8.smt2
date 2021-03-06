(declare-rel inv (Int Int Int Int Int Int))
(declare-var a Int)
(declare-var a1 Int)
(declare-var b Int)
(declare-var b1 Int)
(declare-var c Int)
(declare-var c1 Int)
(declare-var d Int)
(declare-var d1 Int)
(declare-var e Int)
(declare-var e1 Int)
(declare-var f Int)
(declare-var f1 Int)

(rule (inv 0 0 0 0 0 0))

(rule (=> 
    (and 
        (inv a b c d e f)
        (= a 0)
        (= a1 (+ a b))
        (= b1 (+ b c))
        (= c1 (+ c d))
        (= d1 (+ d e))
        (= e1 (+ e f))
        (= f1 (+ f 1))
    )
    (inv a1 b1 c1 d1 e1 f1)
  )
)
