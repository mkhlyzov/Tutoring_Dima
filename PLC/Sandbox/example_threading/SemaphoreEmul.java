public class SemaphoreEmul {
    ReentrantLock lock = new ReentrantLock();
    ReentrantLock lock2 = new ReentrantLock();
    static Object monitor = new Object();
    Object monitor2 = new Object();
    void f1() {
        lock.lock();
        ...
        lock.unlock();
    }
    void f11() {
        lock2.lock();
        ...
        lock2.unlock();
    }
    void f2() {
        synchronized(this.getClass()) {
            ...
        }
    }
    static synchronized void f3() {
        ...
    }
    void f4() {
        synchronized(monitor) {
            ...
        }
    }
    void f5() {
        synchronized(monitor2) {
            ...
        }
    }

    void main() {
        SemaphoreEmul s = new SemaphoreEmul();
        SemaphoreEmul s1 = new SemaphoreEmul();
        s.f4(); s1.f4();
        s.f5(); s1.f5();
    }
}
