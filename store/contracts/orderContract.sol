// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract DeliveryContract {
    address public customer;       //customer
    address payable public courier;
    address payable public owner;
    uint public orderValue;
    uint public deposit;
    bool public courierAssigned;
    bool public deliveryConfirmed;

    uint private orderId;

    constructor (address payable _customer, uint _orderValue){
        owner = payable(msg.sender);
        customer = _customer;
        orderValue = _orderValue;
    }

    modifier onlyCustomer() {
        require(msg.sender == customer, "Only contract owner can call this function.");
        _;
    }

    modifier onlyOwner() {  ///vrv visak
        require(msg.sender == owner, "Only customer can call this function.");
        _;
    }

    modifier onlyCourier() {
        require(msg.sender == courier, "Only courier can call this function.");
        _;
    }

    modifier onlyBeforeDeliveryConfirmed() {
        require(!deliveryConfirmed, "Delivery is already confirmed.");
        _;
    }

    modifier onlyAfterCourierAssigned() {
        require(courierAssigned, "Courier is not assigned yet.");
        _;
    }

    function getCustomer() public view returns (address){
        return customer;
    }

    function getCourier() public view returns (address){
        return courier;
    }

    function getDeposit() public view returns (uint){
        return deposit;
    }

    function assignCourier(address payable _courier) public onlyBeforeDeliveryConfirmed {
        courier = _courier;
        courierAssigned = true;
    }

    function depositFunds() public payable onlyCustomer onlyBeforeDeliveryConfirmed {
        require(msg.value == orderValue, "Incorrect deposit amount.");
        deposit = msg.value;
    }

    function confirmDelivery() public onlyCustomer onlyAfterCourierAssigned onlyBeforeDeliveryConfirmed {
        deliveryConfirmed = true;
        uint ownerAmount = (deposit * 80) / 100;
        uint courierAmount = (deposit * 20) / 100;
        owner.transfer(ownerAmount);
        courier.transfer(courierAmount);
    }
}
