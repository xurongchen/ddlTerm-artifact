function {:existential true} b0(x:int, y:int, z:int %FD%, TR1:int, TR2:int): bool;

procedure main()
{
  var x,y,z %VD%, TR1, TR2: int;
  havoc x;
  havoc y;
  havoc z;

  %BE%
TR1 := 0;
TR2 := 0;

  while (x >= 0)
  invariant b0(x,y,z %IC%, TR1, TR2);
  {
    %BT%
TR1 := 0;
TR2 := 0;
    if (*) {
TR1 := 1;
        x := x + y;
    } else {
TR2 := 1;
        x := x + z;
    }
    y := y + z;
    z := z - 1;
    %IT%
  }
}
