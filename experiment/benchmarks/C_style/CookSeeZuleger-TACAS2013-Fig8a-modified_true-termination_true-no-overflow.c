extern int __VERIFIER_nondet_int(void);

int main() {
    int K, x;
    K = __VERIFIER_nondet_int();
    x = __VERIFIER_nondet_int();
    while (x != K) {
        if (x > K) {
            x = x - 1;
        } else {
            x = x + 1;
        }
    }
    return 0;
}
