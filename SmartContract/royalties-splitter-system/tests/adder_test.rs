use royalties_splitter_system::*;
use elrond_wasm::types::BigUint;
use elrond_wasm_debug::DebugApi;

#[test]
fn test_add() {
    let _ = DebugApi::dummy();

    let adder = royalties_splitter_system::contract_obj::<DebugApi>();

    adder.init(BigUint::from(5u32));
    assert_eq!(BigUint::from(5u32), adder.sum().get());

    let _ = adder.add(BigUint::from(7u32));
    assert_eq!(BigUint::from(12u32), adder.sum().get());

    let _ = adder.add(BigUint::from(1u32));
    assert_eq!(BigUint::from(13u32), adder.sum().get());
}
