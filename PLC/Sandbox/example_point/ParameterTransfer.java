package PLC.Sandbox.example_point;

public class ParameterTransfer {
   static void setRadius(double r, Circle c) {
      c.radius = r; r = 0; c = null;
   }
   public static void main(String[] args) {
      double maxr = 100.0;
      Circle c    = new Circle(1.0,1.0,1.0);
      setRadius(maxr, c);
      System.out.println("maxr = " + maxr);
      System.out.println("c.radius = " + c.radius);
   }
}