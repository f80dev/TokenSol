<?php

function api($url,$args){
  $content = json_encode($args);

  $curl = curl_init($url);
  curl_setopt($curl, CURLOPT_HTTPHEADER,array("Content-type: application/json"));
  curl_setopt($curl, CURLOPT_POST, true);
  curl_setopt($curl, CURLOPT_POSTFIELDS, $content);

  $json_response = curl_exec($curl);

  $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);
  echo("status=".$status);

  curl_close($curl);

  return $response = json_decode($json_response, true);
}


$args=array(
  "email" => "paul.dudule@gmail.com",
  "title" => "David52",
  "miner" => "paul",
  "collection" => "nfluent",
  "properties" => "",
  "quantity" => 1,
  "royalties" => 10,
  "visual" => "image1.gif",
  "network" => "elrond-devnet"
);

echo(print_r($args));

//$url='https://server.f80lab.com:4242/api/mint_from_prestashop/';
$url='http://127.0.0.1:4242/api/mint_for_prestashop/';


echo(print_r(api($url,$args)));



?>
