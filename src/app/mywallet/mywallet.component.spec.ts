import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MywalletComponent } from './mywallet.component';
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {RouterTestingModule} from "@angular/router/testing";

describe('MywalletComponent', () => {
  let component: MywalletComponent;
  let fixture: ComponentFixture<MywalletComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MywalletComponent ],
      imports: [HttpClientModule,MatSnackBarModule,RouterTestingModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MywalletComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
