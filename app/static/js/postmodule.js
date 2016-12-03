angular.module('myApp', [])
.controller('myCtrl', function ($scope, $http) {
    $scope.dbAddress = "";
    $scope.tables = {}
    $scope.selectedTableName = "";
    $scope.selectedStartRow = 0;
    $scope.selectedTableData = [];
    $scope.selectedTableDataHeader = [];
    $scope.orderColName = null;
    $scope.orderAscending = false;
    
    $scope.toggleColSort = function(colname){
    	if (colname != $scope.orderColName){
    		$scope.orderAscending = false;  // will be set to true below
    	}
    	$scope.orderColName = colname;
    	$scope.orderAscending = !$scope.orderAscending;
    	$scope.queryTable();
    }
    
    $scope.queryDb = function() {
        var data = {
        	url: $scope.dbAddress
        };
        $http.post("/query_db", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}).success(function(data, status) {
        	$scope.selectedStartRow = 0;
        	$scope.selectedTableName = "";
        	$scope.selectedTableData = [];
        	$scope.selectedTableDataHeader = [];
            for(var i=0; i<data.length; i++){
            	$scope.tables[data[i][0]] = data[i][1];
            }
            var g = 9;
        });
    }
    $scope.setSelectedTableName = function(tableName){
    	$scope.selectedTableName = tableName;
    	$scope.queryTable();
    }
    $scope.queryTable = function() {
        var data = {
        	name: $scope.selectedTableName,
        	start_row: 0,
        	num_results: 20,
        	order_colname: $scope.orderColName,
        	order_ascending: $scope.orderAscending
        };
        $http.post("/query_table", JSON.stringify(data),
        		{headers: {'Content-Type': 'application/json'}}).success(function(data, status) {
        	$scope.selectedTableData = data.slice(2);
        	$scope.selectedTableDataHeader = data.slice(0, 2);
        });
    }
    
})
