function {:existential true} b0(x:int, y:int %FD%): bool;

procedure main()
{
  var x,y %VD%: int;
  havoc x;
  havoc y;

  assume(!(x <= 0 || y <= 0));
  %BE%

  while (x + y > 0)
  invariant b0(x,y %IC%);
  {
    %BT%
    x := -4*x + 18;
    y := -6*y + 13;
    %IT%
  }
}
