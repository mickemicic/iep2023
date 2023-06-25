// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract DeliveryContract {
    address payable public contractOwner;       //customer
    address payable public courier;
    address public owner;
    uint public orderValue;
    uint public deposit;
    bool public courierAssigned;
    bool public deliveryConfirmed;

    uint private orderId;

    constructor (uint _orderId, address _owner, uint _orderValue){
        orderId = _orderId;
        contractOwner = payable(msg.sender);
        owner = _owner;
        orderValue = _orderValue;
    }

    modifier onlyContractOwner() {
        require(msg.sender == contractOwner, "Only contract owner can call this function.");
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

    function getContractOwner() public view returns (address){
        return contractOwner;
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
