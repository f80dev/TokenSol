<?php
/**
 * 2007-2022 PrestaShop
 *
 * NOTICE OF LICENSE
 *
 * This source file is subject to the Academic Free License (AFL 3.0)
 * that is bundled with this package in the file LICENSE.txt.
 * It is also available through the world-wide-web at this URL:
 * http://opensource.org/licenses/afl-3.0.php
 * If you did not receive a copy of the license and are unable to
 * obtain it through the world-wide-web, please send an email
 * to license@prestashop.com so we can send you a copy immediately.
 *
 * DISCLAIMER
 *
 * Do not edit or add to this file if you wish to upgrade PrestaShop to newer
 * versions in the future. If you wish to customize PrestaShop for your
 * needs please refer to http://www.prestashop.com for more information.
 *
 *  @author    PrestaShop SA <contact@prestashop.com>
 *  @copyright 2007-2022 PrestaShop SA
 *  @license   http://opensource.org/licenses/afl-3.0.php  Academic Free License (AFL 3.0)
 *  International Registered Trademark & Property of PrestaShop SA
 */

global $smarty;

if (!defined('_PS_VERSION_')) {
  exit;
}

class NFLUENT extends Module
{
  protected $config_form = false;



  public function __construct()
  {
    $this->name = 'NFLUENT';
    $this->tab = 'administration';
    $this->version = '1.0.5';
    $this->author = 'NFLUENT';
    $this->need_instance = 1;

    /**
     * Set $this->bootstrap to true if your module is compliant with bootstrap (PrestaShop 1.6)
     */
    $this->bootstrap = true;

    parent::__construct();

    $this->displayName = $this->l('NFT module');
    $this->description = $this->l('Vendez des NFT directement depuis votre boutique');

    $this->ps_versions_compliancy = array('min' => '1.6', 'max' => _PS_VERSION_);
  }

  /**
   * Don't forget to create update methods if needed:
   * http://doc.prestashop.com/display/PS16/Enabling+the+Auto-Update
   */
  public function install()
  {
    Configuration::updateValue('NFLUENT_LIVE_MODE', false);

//        Liste des evenements : https://devdocs.prestashop.com/1.7/modules/concepts/hooks/list-of-hooks/

    return parent::install() &&
      $this->registerHook('header') &&
      $this->registerHook('backOfficeHeader') &&
      $this->registerHook('actionPaymentConfirmation') &&
      $this->registerHook('actionOrderStatusPostUpdate');
  }

  public function uninstall()
  {
    Configuration::deleteByName('NFLUENT_LIVE_MODE');

    return parent::uninstall();
  }



  /**
   * Load the configuration form
   */
  public function getContent()
  {
    /**
     * If values have been submitted in the form, process.
     */
    if (((bool)Tools::isSubmit('ServerConfigForm')) == true) {
      $this->postProcess();
    }

    $this->context->smarty->assign('module_dir', $this->_path);

    $output = $this->context->smarty->fetch($this->local_path.'views/templates/admin/configure.tpl');

    return $output;
  }

  /**
   * Create the form that will be displayed in the configuration of your module.
   */
  protected function renderForm()
  {
    $helper = new HelperForm();

    $helper->show_toolbar = false;
    $helper->table = $this->table;
    $helper->module = $this;
    $helper->default_form_language = $this->context->language->id;
    $helper->allow_employee_form_lang = Configuration::get('PS_BO_ALLOW_EMPLOYEE_FORM_LANG', 0);

    $helper->identifier = $this->identifier;
    $helper->submit_action = 'submitNFLUENTModule';
    $helper->currentIndex = $this->context->link->getAdminLink('AdminModules', false)
      .'&configure='.$this->name.'&tab_module='.$this->tab.'&module_name='.$this->name;
    $helper->token = Tools::getAdminTokenLite('AdminModules');

    $helper->tpl_vars = array(
      'fields_value' => $this->getConfigFormValues(), /* Add values for your inputs */
      'languages' => $this->context->controller->getLanguages(),
      'id_language' => $this->context->language->id,
    );

    return $helper->generateForm(array($this->getConfigForm()));
  }

  /**
   * Create the structure of your form.
   */
  protected function getConfigForm()
  {
    return array(
      'form' => array(
        'legend' => array(
          'title' => $this->l('Settings'),
          'icon' => 'icon-cogs',
        ),
        'input' => array(
          array(
            'type' => 'switch',
            'label' => $this->l('Live mode'),
            'name' => 'NFLUENT_LIVE_MODE',
            'is_bool' => true,
            'desc' => $this->l('Use this module in live mode'),
            'values' => array(
              array(
                'id' => 'active_on',
                'value' => true,
                'label' => $this->l('Enabled')
              ),
              array(
                'id' => 'active_off',
                'value' => false,
                'label' => $this->l('Disabled')
              )
            ),
          ),
          array(
            'col' => 3,
            'type' => 'text',
            'prefix' => '<i class="icon icon-envelope"></i>',
            'desc' => $this->l('Enter a valid email address'),
            'name' => 'NFLUENT_ACCOUNT_EMAIL',
            'label' => $this->l('Email'),
          ),
          array(
            'type' => 'password',
            'name' => 'NFLUENT_ACCOUNT_PASSWORD',
            'label' => $this->l('Password'),
          ),
        ),
        'submit' => array(
          'title' => $this->l('Save'),
        ),
      ),
    );
  }

  /**
   * Set values for the inputs.
   */
  protected function getConfigFormValues()
  {
    $server_addr=(string) Tools::getValue('SERVER_ADDR');
    Logger::AddLog("Enregistrement de ".$server_addr);
    return array(
      'NFLUENT_LIVE_MODE' => Configuration::get('NFLUENT_LIVE_MODE', true),
      'NFLUENT_ACCOUNT_EMAIL' => Configuration::get('NFLUENT_ACCOUNT_EMAIL', 'contact@nfluent.io'),
      'NFLUENT_SERVER_ADDRESS' => $server_addr,
      'NFLUENT_ACCOUNT_PASSWORD' => Configuration::get('NFLUENT_ACCOUNT_PASSWORD', null),
    );
  }

  /**
   * Save form data.
   */
  protected function postProcess()
  {
    $form_values = $this->getConfigFormValues();

    foreach (array_keys($form_values) as $key) {
      Configuration::updateValue($key, Tools::getValue($key));
    }
  }

  /**
   * Add the CSS & JavaScript files you want to be loaded in the BO.
   */
  public function hookBackOfficeHeader()
  {
    if (Tools::getValue('module_name') == $this->name) {
      $this->context->controller->addJS($this->_path.'views/js/back.js');
      $this->context->controller->addCSS($this->_path.'views/css/back.css');
    }
  }

  /**
   * Add the CSS & JavaScript files you want to be added on the FO.
   */
  public function hookHeader()
  {
    $this->context->controller->addJS($this->_path.'/views/js/front.js');
    $this->context->controller->addCSS($this->_path.'/views/css/front.css');
  }






  public function api($url,$args){
    Logger::AddLog("Appel de ".$url);
    $payload  = json_encode($args);

    Logger::AddLog("Arguments: ".$payload);
    $curl = curl_init($url);
    curl_setopt($curl, CURLOPT_HTTPHEADER,array("Content-type: application/json"));
    curl_setopt($curl, CURLOPT_POST, true);
    curl_setopt($curl, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($curl, CURLOPT_SSL_VERIFYPEER , false);
    $json_response = curl_exec($curl);

    $state = curl_getinfo($curl,"CURLINFO_HTTP_CODE");
    $err     = curl_error( $curl );
    Logger::AddLog("Error: ".$err);

    $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    //Logger::AddLog("status ".$status);

    curl_close($curl);

    Logger::AddLog("reponse ".print_r($json_response));
    $response = json_decode($json_response, true);


    return $response;
  }





  //Fonction appelant le minage mint_for_prestashop
  public function hookActionOrderStatusPostUpdate($params){

    $newOrderStatus = $params['newOrderStatus'];
    Logger::AddLog("hookActionOrderStatusPostUpdate. argument=".$newOrderStatus->name);

    if($newOrderStatus->name=="Expédié" && $newOrderStatus->paid){
      //pour $newOrderStatus voir https://devdocs.prestashop.com/1.7/webservice/resources/order_states/

      //La ressource order : https://devdocs.prestashop.com/1.7/webservice/resources/orders/
      $order= new Order($params['id_order']);

      //La ressource customer : https://devdocs.prestashop.com/1.7/webservice/resources/customers/
      $customer=new Customer($order->id_customer);

      //Voir https://devdocs.prestashop.com/1.7/webservice/resources/products/
      $products=$order->getCartProducts();

      Logger::AddLog("Recupration des produits. argument=".implode(" ",$products));

      foreach ($products as $product){
        $dest=$customer->email;
        $category=new Category($product["id_category_default"]);

        $args=array(
          "email" => $dest,
          "quantity" => 1,
          "order_status" => $newOrderStatus->name,
          "product" => $product,
          "address" => $customer->note,
          "customer" => $customer->id,
        );
        Logger::AddLog("Envoi des arguments=".implode(" ",$args));

        $store_addr=$smarty->tpl_vars['base_dir']->value;
        Logger::AddLog("Address de la boutique = ".$store_addr);

        //$url='https://server.f80lab.com:4242/api/mint_from_prestashop/';
        //if($store_addr.strpos("127.0.0.1")>0)
        $url='http://host.docker.internal:4242/api/mint_from_prestashop/';  #host.docker.internal designe le localhost

        $resp=$this->api($url,$args);
        if($resp->result=="ok"){
          Logger::AddLog("Changement de statut pour livré");
          $history = new OrderHistory();
          $history->id_order = $params['id_order'];
          $history->changeIdOrderState('5', $params['id_order']);

          //Voir
          Logger::AddLog("Ecriture de l'adresse ".$resp->address." dans le compte client");

          //TODO faire la mise a jour du client avec son adresse blockchain
          //TODO faire la mise a jour de l'order avec l'adresse de mint
        }

      }
    }

  }

  public function hookActionPaymentConfirmation($params){

  }



}
