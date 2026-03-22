class RNG {
	public static void main(String[] args) {
		long multiplier = 0x5DEECE66DL;
		long addend = 0xBL;
		long mask = (1L << 48) - 1;


		System.out.println("multiplier " + multiplier);
		System.out.println("addent     " + addend);
		System.out.println("mask       " + mask);
		System.out.println();
		printBinary(multiplier);
		printBinary(addend);
		printBinary(1L);
		printBinary(mask);
	}

	public static void printBinary(long  num) {
		for (int i = 48; i >= 0; i--) {
			System.out.print((num >>> i) & 1);
		}
		System.out.println();
	}
}