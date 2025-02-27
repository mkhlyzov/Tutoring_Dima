// package PLC.Sandbox.example_threading;

import java.util.concurrent.Semaphore;

public class FieldWork {
    public int processed_area = 0;
    static Semaphore semaphore = new Semaphore(1);

    FieldWork() {
        processed_area = 0;
    }

    public void work_the_field_once() {
        try {semaphore.acquire();}
        catch (InterruptedException e) {e.printStackTrace();}

        processed_area++;
        // processed_area = processed_area + 1;
        semaphore.release();
    }

    public void work_for_a_farmer() {
        for (int i = 0; i < 1_000_000; i++) {
            work_the_field_once();
        }
    }

    public static void main(String[] args) {
        FieldWork fieldWork = new FieldWork();

        Thread[] farmers = new Thread[10];
        for (int i = 0; i < farmers.length; i++) {
            farmers[i] = new Thread(fieldWork::work_for_a_farmer);
            farmers[i].start();
        }

        // try {
        //     Thread.sleep(100);            
        // } catch (InterruptedException e) {
        //     e.printStackTrace();
        // }

        for (int i = 0; i < farmers.length; i++) {
            try {
                farmers[i].join();
            } catch (InterruptedException e) {
                e.printStackTrace();
            }
        }
        System.out.println(fieldWork.processed_area); // should be 10_000_000
    }
}
