import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MintComponent } from './mint.component';
import {MatSnackBar, MatSnackBarModule} from "@angular/material/snack-bar";
import {HttpClientModule} from "@angular/common/http";
import {MatDialogModule} from "@angular/material/dialog";
import {RouterTestingModule} from "@angular/router/testing";

describe('MintComponent', () => {
  let component: MintComponent;
  let fixture: ComponentFixture<MintComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MintComponent ],
      imports: [MatSnackBarModule,HttpClientModule,MatDialogModule,RouterTestingModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(MintComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
