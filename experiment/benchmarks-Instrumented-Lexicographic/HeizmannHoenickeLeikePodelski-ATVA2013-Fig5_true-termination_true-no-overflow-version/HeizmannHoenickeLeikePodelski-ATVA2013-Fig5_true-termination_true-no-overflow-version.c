#include <stdio.h>

int main()
{
    int x;
    scanf("%d", &x);
    printf("[Testing] <Interface V3.0TR> (Basic lexical method)\n");

    int y = 3;
    while (x >= 0)
    {
        printf("%d\n", y);
        x = x - y;
        y = (y + 2) / 3;
    }
    return 0;
}
