<?php

function api2($args){
  $url='https://server.f80lab.com:4242/api/mint_from_prestashop/';

  $content = json_encode($args);

  $curl = curl_init($url);
  curl_setopt($curl, CURLOPT_HEADER, false);
  curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
  curl_setopt($curl, CURLOPT_HTTPHEADER,array("Content-type: application/json"));
  curl_setopt($curl, CURLOPT_POST, true);
  curl_setopt($curl, CURLOPT_POSTFIELDS, $content);

  $json_response = curl_exec($curl);

  $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);

  curl_close($curl);

  return $response = json_decode($json_response, true);
}


$args=array(
  "email" => "paul.dudule@gmail.com",
  "product_name" => "LP154L",
  "product_ref" => "ref"
);

api2($args);
echo(print_r($args));


?>
