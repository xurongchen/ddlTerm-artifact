function {:existential true} b0(x:int, y:int %FD%, TR1:int, TR2:int, TR3:int, TR4:int): bool;

procedure main()
{
  var x,y,z %VD%, TR1, TR2, TR3, TR4: int;

  havoc x;
  havoc y;

  %BE%
TR1 := 0;
TR2 := 0;
TR3 := 0;
TR4 := 0;
  	
  while (y > 0 && x > 0)
  invariant b0(x,y %IC%, TR1, TR2, TR3, TR4);
  {
    %BT%
TR1 := 0;
TR2 := 0;
TR3 := 0;
TR4 := 0;
    if (x > y)
    {
TR1 := 1;
        z := y;
    }
    else
    {
TR2 := 1;
        z := x;
    }
    if (*)
    {
TR3 := 1;
        y := y + x;
        x := z - 1;
        z := y + z;
    }
    else
    {
TR4 := 1;
        y := y + x;
        x := z - 1;
        z := x + z;
    }
    
    %IT%
  }
}
