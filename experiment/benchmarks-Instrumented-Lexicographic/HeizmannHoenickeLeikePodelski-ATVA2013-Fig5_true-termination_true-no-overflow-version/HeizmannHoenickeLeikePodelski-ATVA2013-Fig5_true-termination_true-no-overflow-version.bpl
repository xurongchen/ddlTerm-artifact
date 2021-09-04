function {:existential true} b0(x:int, y:int %FD%): bool;

procedure main()
{
  var x,y %VD%: int;

  havoc x;
  
  y := 3;

  %BE%
  	
  while (x >= 0)
  invariant b0(x,y %IC%);
  {
    %BT%
		x := x - y;
		y := (y + 2) div 3;

    %IT%
  }
}
