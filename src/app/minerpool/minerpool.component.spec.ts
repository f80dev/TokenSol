import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MinerpoolComponent } from './minerpool.component';
import {HttpClientModule} from "@angular/common/http";

describe('MinerpoolComponent', () => {
  let component: MinerpoolComponent;
  let fixture: ComponentFixture<MinerpoolComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MinerpoolComponent ],
      imports: [HttpClientModule]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MinerpoolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
