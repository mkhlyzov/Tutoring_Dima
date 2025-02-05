use std::mem;

fn main() {
    // let x: u8 = 5;
    // let b: bool = true;
    // if (x) {
    //     println!("sdfsd");
    // }
    println!(
        "{}, {}",
        mem::size_of::<bool>(),
        mem::size_of::<u8>()
    );
}