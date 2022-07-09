<?php
if (!defined('_PS_VERSION_')) {
  exit;
}

class nFluent extends Module
{
  public function __construct()
  {
    $this->name = 'mymodule';
    $this->tab = 'back_office_features';
    $this->version = '1.0.0';
    $this->author = 'Herve HOAREAU';
    $this->need_instance = 0;
    $this->ps_versions_compliancy = [
      'min' => '1.6',
      'max' => '1.7.99',
    ];
    $this->bootstrap = true;

    parent::__construct();

    $this->displayName = $this->l('nFluent Module');
    $this->description = $this->l('Ce module permet la vente de NFT depuis prestashop');

    $this->confirmUninstall = $this->l('Are you sure you want to uninstall?');

    if (!Configuration::get('NFLUENT_MODULE')) {
      $this->warning = $this->l('No name provided');
    }
  }

  public function uninstall()
  {
    return (
      parent::uninstall()
      && Configuration::deleteByName('NFLUENT_MODULE')
    );
  }

  public function install()
  {
    if (Shop::isFeatureActive()) {
      Shop::setContext(Shop::CONTEXT_ALL);
    }

    return (
      parent::install()
      && $this->registerHook('hookActionValidateOrder')
      && Configuration::updateValue('MYMODULE_NAME', 'my friend')
    );
  }

  public function hookActionValidateOrder($params){
    Logger::AddLog("A new order has been submitted. Data : ".print_r($params));
    /*
    *
    * More stuff here, but i need the order data
    *
    */
  }

}

?>
