#include <stdio.h>
#include <stdlib.h>

int main()
{
    int x, y, old_x, old_y;
    scanf("%d%d", &x, &y);
    printf("[Testing] <Interface V4.0> (Log all variables for reuse)\n");

    while (x > 0 && y > 0)
    {
        printf("x:%d,y:%d,old_x:%d,old_y:%d\n", x, y, old_x, old_y);

        old_x = x;
        old_y = y;
        x = old_y - 2;
        y = old_x + 1;
    }
    return 0;
}
