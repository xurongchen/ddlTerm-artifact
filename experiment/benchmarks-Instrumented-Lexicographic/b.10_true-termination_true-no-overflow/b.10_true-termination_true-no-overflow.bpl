function {:existential true} b0(x:int, y:int %FD%, TR1:int, TR2:int, TR3:int, TR4:int): bool;

procedure main()
{
  var x,y %VD%, TR1, TR2, TR3, TR4: int;
  havoc x;
  havoc y;
  
  %BE%
TR1 := 0;
TR2 := 0;
TR3 := 0;
TR4 := 0;
  
  while (((x >= 0 && y < 2147483647 - x) || (x < 0 && y > -2147483648 - x)) && x + y > 0)
  invariant b0(x,y %IC%, TR1, TR2, TR3, TR4);
  {
    %BT%
TR1 := 0;
TR2 := 0;
TR3 := 0;
TR4 := 0;
    if (x > 0){
TR1 := 1;
      x := x - 1;
    }
    else {
TR2 := 1;
      if (y > 0){
TR3 := 1;
        y := y - 1;
      }
      else {
TR4 := 1;
        
      }
    }
    %IT%
  }
}
